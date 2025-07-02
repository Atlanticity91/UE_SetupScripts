#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys
import psutil

# Target folders to delete
folders = [
	".vs",
	"Binaries",
	"DerivedDataCache",
	"Intermediate",
	"Saved"
]

def is_process_running( process_name ) :
	for process in psutil.process_iter( ['name'] ):
		if process.info[ 'name' ].lower( ) == process_name.lower( ) :
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
		print( "\033[31m> Can't find epic games installation directory as EPIC_DIR environement variable.\033[0m" )

		sys.exit( 1 )

	full_path = os.path.join( epic_path, engine_version )

	if not os.path.isdir( full_path ) :
		print( f'\033[31m> Invalid unreal engine path :{full_path}\033[0m' )

		sys.exit( 1 )

	return full_path

'''
	clear_directory function
	@note : Clear the target path by removing any folder present in folders array.
	@param target_path : Target path to clear
'''
def clear_directory( target_path ) :
	for path_name in os.listdir( target_path ) :
		full_path = os.path.join( target_path, path_name )

		if os.path.isdir( full_path ) :
			if path_name in folders :
				print( f'\033[33m> Removed {full_path}\033[0m' )

				shutil.rmtree( full_path )
		elif os.path.splitext( path_name )[ -1 ].lower( ) == '.sln' :
			print( f'\033[33m> Removed {full_path}\033[0m' )

			os.remove( full_path )

'''
	clean_project function
	@note : Clean a project path by removing any folder present in folders array from
			target project/plugins path.
	@param project_path : Target project path to clear.
'''
def clean_project( project_path ) :
	root_path = os.path.dirname( project_path )

	clear_directory( root_path )

	plugin_path = os.path.join( root_path, 'Plugins' )

	if not os.path.exists( plugin_path ) :
		print( f"\033[31m> Can't find plugins directory : {plugin_path}\033[0m" )

		return

	for plugin_name in os.listdir( plugin_path ) :
		full_path = os.path.join( plugin_path, plugin_name )

		clear_directory( full_path )

'''
	create_project function
	@note : Make the call to UnrealBuildTool to make the target project solution
	@param engine_path : Target current project engine path.
	@param project_path : Target current project uproject path.
'''
def create_project( engine_path, project_path ) :
	build_script = os.path.join( engine_path, 'Engine', 'Binaries', 'DotNET', 'UnrealBuildTool', 'UnrealBuildTool.dll' )

	if not os.path.isfile( build_script ) :
		print( f"\033[31m> Can't find build script {build_script}\033[0m" )

		sys.exit( 1 )

	result = subprocess.run([ 'dotnet', build_script, '-ProjectFiles', f'-Project={project_path}', '-Game', '-Engine', '-Progress' ], shell=True )

	if result.returncode == 0 :
		print( '\033[32m> Project files regenerated.\033[0m' )
	else :
		print( '\033[31m> Project files reneration failed.\033[0m' )

'''
	main function
	@mote : Script main function ot execute using argparse for argument parsing.
			Use --engine for engine version.
			Use --project for project path.
			Both are required for cleaning and solution creation.
'''
def main( ) :
	parser = argparse.ArgumentParser( description='Clean and Regenerate unreal engine project files.' )
	parser.add_argument( '--engine', required=True, help='Unreal engine folder name (e.g UE_5.4)' )
	parser.add_argument( '--project', required=True, help='Project .uproject path' )

	args = parser.parse_args( )

	engine_path = resolve_engine_path( args.engine )
	project_path = os.path.abspath( args.project )

	if is_process_running( 'devenv.exe' ) :
		print( '\033[31m> Please close visual studio before executing the script.\033[0m' )

		sys.exit( 1 )

	for editor in [ 'UE4Editor.exe', 'UnrealEditor.exe' ] :
		if is_process_running( editor ) :
			print( '\033[31m> Please close unreal editor before executing the script.\033[0m' )

			sys.exit( 1 )

	if not os.path.isfile( project_path ) :
		print( "\033[31m> Target project path isn't valid\033[0m" )

		sys.exit( 1 )

	clean_project( project_path )
	create_project( engine_path, project_path )

if __name__ == "__main__" :
	main( )
