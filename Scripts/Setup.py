#!/usr/bin/env python3

import argparse
import os
import shutil
import stat
import subprocess
import sys
import psutil
import json

# Target folders to delete
folders = [
	".vs",
	"Binaries",
	"DerivedDataCache",
	"Intermediate",
	"Saved"
]

'''
    print_log method
    @brief Print log with color to terminal.
    @param message Targeted message to print.
    @param color Targeted color for the print.
'''
def print_log( message, color=None ) :
	if color :
		print( f'\x1b[{color}m{message}\x1b[0m' )
	else :
		print( message )

def print_message( message ) : print_log( message, None )
def print_succ( message ) : print_log( message, 32 )
def print_warn( message ) : print_log( message, 33 )
def print_errr( message ) : print_log( message, 31 )

'''
	is_process_running function
	@brief : Check if a process with process_name is currently running.
	@param process_name : Target process name.
	@return Process from psutil or None if no process found.
'''
def is_process_running( process_name ) :
	for process in psutil.process_iter( [ 'name', 'cmdline' ] ):
		try : 
			if process_name.lower( ) not in process.info[ 'name' ].lower( ) :
				continue
			
			return process
		except ( psutil.NoSuchProcess, psutil.AccessDenied ) :
			continue

	return None

'''
	is_running_vs_solution function
	@brief : Check if the current project solution is opened in visual studio.
	@param uproject_path : Target uproject path.
	@return True when visual studio is running the solution.
'''
def is_running_vs_solution( uproject_path ) :
	process = is_process_running( 'devenv.exe' )

	if process is not None :
		args = process.info.get( 'cmdline', [ ] )

		# TODO : Specific check, for now consider all vs instance to run the solution.

		print_errr( '> Please close visual studio before executing the script.' )

		return True

	return False

'''
	is_running_ue_solution function
	@brief : Check if the current project solution is opened in unreal engine editor.
	@param uproject_path : Target uproject path.
	@return True when unreal engine editor is running the solution.
'''
def is_running_ue_solution( uproject_path ) :
	solution = os.path.basename( uproject_path ).lower( )

	for editor in [ 'UE4Editor.exe', 'UnrealEditor.exe' ] :
		process = is_process_running( editor )

		if process is not None :
			for argument in process.info.get( 'cmdline', [ ] ) :
				if solution in argument.lower( ) :
					print_errr( '> Please close unreal editor before executing the script.' )

					return True

	return False

'''
	resolve_engine_path function
	@param engine_version Target engine version.
	@return Return final engine path to the query engine version.
'''
def resolve_engine_path( engine_version ) :
	epic_path = os.environ.get( 'EPIC_DIR' )

	if not epic_path :
		print_errr( '> Can\'t find epic games installation directory as EPIC_DIR environement variable.' )

		sys.exit( 1 )

	full_path = os.path.join( epic_path, engine_version )

	if not os.path.isdir( full_path ) :
		print_errr( f'> Invalid unreal engine path :{full_path}' )

		sys.exit( 1 )

	return full_path

'''
	resolve_project_path function
	@param arg_path Target .uproject file path.
	@return .uproject root path.
'''
def resolve_project_path( arg_path ) :
	if not os.path.isfile( arg_path ) :
		print_errr( '> Target uproject path isn\'t valid' )

		sys.exit( 1 )

	project_path, project_ext = os.path.splitext( arg_path )

	if not project_ext.lower( ) == ".uproject" :
		print_errr( '> Target uproject path isn\'t valid' )

		sys.exit( 1 )

	return os.path.dirname( project_path )

'''
	clear_directory function
	@brief : Clear the target path by removing any folder present in folders array.
	@param target_path : Target path to clear
'''
def clear_directory( target_path ) :
	for path_name in os.listdir( target_path ) :
		full_path = os.path.join( target_path, path_name )

		if os.path.isdir( full_path ) :
			if path_name in folders :
				print_warn( f'> Removed {full_path}' )

				shutil.rmtree( full_path )
		elif os.path.splitext( path_name )[ -1 ].lower( ) == '.sln' :
			print_warn( f'> Removed {full_path}' )

			os.remove( full_path )

'''
	get_plugins_path function
	@brief : Concatenate root_path + 'Plugins'
'''
def get_plugins_path( root_path ) :
	return os.path.join( root_path, 'Plugins' )

'''
	clean_project function
	@brief : Clean a project path by removing any folder present in folders array from
			target project/plugins path.
	@param project_path : Target project path to clear.
'''
def clean_project( project_path ) :
	print_message( '> Cleaning project solution folder' )

	clear_directory( project_path )

	plugins_path = get_plugins_path( project_path )

	if not os.path.exists( plugins_path ) :
		print_errr( f'> Can\'t find plugins directory : {plugins_path}' )

		return

	for plugin_name in os.listdir( plugins_path ) :
		full_path = os.path.join( plugins_path, plugin_name )

		clear_directory( full_path )

'''
	create_project function
	@brief : Make the call to UnrealBuildTool to make the target project solution
	@param engine_path : Target current project engine path.
	@param project_path : Target current project uproject path.
'''
def create_project( engine_path, project_path ) :
	build_script = os.path.join( engine_path, 'Engine', 'Binaries', 'DotNET', 'UnrealBuildTool', 'UnrealBuildTool.dll' )

	if not os.path.isfile( build_script ) :
		print_errr( f'> Can\'t find build script {build_script}' )

		sys.exit( 1 )

	print_message( '> Create project solution with UBT :' )

	result = subprocess.run( [ 'dotnet', build_script, '-ProjectFiles', f'-Project={project_path}', '-Game', '-Engine', '-Progress', '-Log=Scripts/Log/UBT_Log.txt' ], shell=True )

	if result.returncode == 0 :
		print_succ( '> UBT Project files regenerated.' )
	else :
		print_errr( '> Project files reneration failed.' )

		sys.exit( 1 )

'''
	extend_solution method
	@brief Extend sln to make each plugins individual project in vs ui.
	@param project_path Target project root path.
'''
def extend_solution( project_path ) :
	print_message( '> Create plugins solution :' )
	 
	plugins_path = get_plugins_path( project_path )

	for plugin_name in os.listdir( plugins_path ) :
		full_path = os.path.join( plugins_path, plugin_name )

		print_message( f'{plugin_name} : {full_path}' )

'''
	copy_git_middleman method
	@brief Copy the GitRules script to .git/hooks/, so the git calls
		   are managed by it and rule branch folder access to prevent
		   unauthorized code modification on non-related folder.
	@param project_path Target project root path.s
'''
def copy_git_middleman( project_path ) :
	print_message( '> Checking Git environment :' )

	hook_path = os.path.join( project_path, '.git' )
	hook_path = os.path.join( hook_path, 'hooks' )
	src_hook = os.path.join( os.path.dirname( __file__ ), 'GitRules.py' )
	dst_hook = os.path.join( hook_path, 'pre-commit' )

	try :
		shutil.copy2( src_hook, dst_hook )

		print_succ( '> Deployement of \'pre-commit\' hook completed.' )

		if os.name != 'nt' :
			file_stat = os.stat( dst_hook )
			os.chmod( dst_hook, file_stat.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH )

			print_succ( '> Permissions of \'pre-commit\' hook applied.' )
	except Exception as e :
		print_errr( f'> Deployement of \'pre-commit\' hook failed :\n{e}' )

'''
	add_git_alias method
	@brief Setup Git alias for rules registration and file validation.
	@param project_path Target project root path.
'''
def add_git_alias( project_path ) :
	def git_register( alias, command ) :
		result = subprocess.run( [ 'git', 'config', f'alias.{alias}', command ] )

		if result.returncode == 0 :
			print_succ( f'> Git alias : \'{alias}\' added.' )
		else :
			print_errr( f'> Cant\'t register git alias : \'{alias}\'.' )
			
			sys.exit( 1 )

	path = os.path.join( project_path, 'Scripts' )
	path = os.path.join( path, 'GitRules.py' )

	git_register( 'addr', f'!addr_f() {{ "{sys.executable}" "{path}" --add-rule "$@"; }}; addr_f' )
	git_register( 'addc', f'!addc_f() {{ "{sys.executable}" "{path}" "$@" && git add "$@"; }}; addc_f' )

'''
	add_git_rules method
	@brief Generate default '.git-rules' content.
	@param project_path Target project root path.
'''
def add_git_rules( project_path ) :
	git_rules_path = os.path.join( project_path, '.git-rules' )
	git_master_rule = { 'master' : [ '.' ] }

	print_message( f'> Added defaults rules : {git_master_rule}' )

	with open( git_rules_path, 'w' ) as f :
		json.dump( git_master_rule, f, indent=4, sort_keys=True )

'''
	setup_git_middleman method
	@brief Do the custom Git setup.
	@param project_path Target project root path.
'''
def setup_git_middleman( project_path ) :
	copy_git_middleman( project_path )
	add_git_alias( project_path )
	add_git_rules( project_path )

'''
	main function
	@brief : Script main function ot execute using argparse for argument parsing.
			Use --engine for engine version.
			Use --project for project path.
			Both are required for cleaning and solution creation.
'''
def main( ) :
	parser = argparse.ArgumentParser( description='Clean and Regenerate unreal engine project files.' )
	parser.add_argument( '--engine', required=True, help='Unreal engine folder name (e.g UE_5.4)' )
	parser.add_argument( '--project', required=True, help='Project .uproject path' )

	args = parser.parse_args( )

	engine_path  = resolve_engine_path( args.engine )
	project_path = resolve_project_path( args.project )

	if is_running_vs_solution( project_path ) or is_running_ue_solution( project_path ) :
		sys.exit( 1 )

	setup_git_middleman( project_path )
	clean_project( project_path )
	create_project( engine_path, args.project )
	extend_solution( project_path )

'''
	Main entry 
'''
if __name__ == "__main__" :
	main( )
