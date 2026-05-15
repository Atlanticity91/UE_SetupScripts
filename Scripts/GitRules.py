#!/usr/bin/env python3

import sys
import subprocess
import json
import os

CONFIG_FILE = '.git-rules'

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
    git_call method
    @param params Parameter list.
    @return Result of 'git prams...' call
'''
def git_call( params ) :
    git_params = [ 'git' ] + params

    return subprocess.run( git_params, capture_output=True, text=True )

'''
    get_current_branch method
    @brief Get current Git branch name.
    @return Current Git branch name.
'''
def get_current_branch( ) :
    result = git_call( [ 'branch', '--show-current' ] )
    branch = result.stdout.strip( )

    if not branch : 
        result = git_call( [ 'symbolic-ref', '--short', 'HEAD' ] )
        branch = result.stdout.strip( )
          
    return branch

'''
    get_staged_files method
    @return Stagged files list.
'''
def get_staged_files( ) :
    result = git_call( [ 'diff', '--cached', '--name-only' ] )
    output = result.stdout.strip( )

    if not output :
        return [ ]

    return output.split( '\n' )

'''
    load_rules method
    @brief Load current rules json.
    @return Current rules json as python object.
'''
def load_rules( ) :
    with open( CONFIG_FILE, 'r' ) as f :
        try :
            return json.load( f )
        except json.JSONDecodeError as e:
            print_errr( f'> Can\'t load \'{CONFIG_FILE}\' :\n{e}' )
            sys.exit( 1 )

'''
    add_rule method
    @brief Add rule for a branch.
    @param args Argument array.
'''
def add_rule( args ) :
    if len( args ) < 3 :
        print_errr( f'> Usage : git addr <branch> <folder>' )

    branch_name = args[ 1 ]
    folder_list = args[ 2: ]
    rules = { }

    if os.path.exists( CONFIG_FILE ) :
        rules = load_rules( )

    if branch_name not in rules :
        rules[ branch_name ] = [ ]

    for folder in folder_list :
        if folder not in rules[ branch_name ] :
            rules[ branch_name ].append( folder )

    try :
        with open( CONFIG_FILE, 'w' ) as f :
            json.dump( rules, f, indent=4 )

        print_succ( f'> Added {folder_list} to branch \'{branch_name}\'' )
    except IOError as e :
        print_errr( f'> Failed to add folders to branch \'{branch_name}\' :\n{e}' )
        sys.exit( 1 )

'''
    parse_file_list method
    @brief Parse the file list to extend '.' and 'folder/.'
    @param file_list List of all files to validate.
'''
def parse_file_list( file_list ) :
    path_list = [ ]

    for file_path in file_list :
        if file_path == '.' or file_path.endswith( './' ) or file_path.endswith( '\\.' ) :
            directory = os.path.rstrip( '.' ).rstrip( '/\\' )
            result = git_call( [ 'ls-files', '--modified', '--others', '--exclude-standard', directory ] )
            files = result.stdout.strip( ).split( '\n' )

            path_list.extend( [ f for f in files if f ] )
        else :
            path_list.append( file_path )

    return path_list

'''
    validate_files method
    @brief Validate files for 'git add' call.
    @param file_list List of all files to validate.
'''
def validate_files( file_list ) :
    file_list = parse_file_list( file_list )
    branch = get_current_branch( )

    if not os.path.exists( CONFIG_FILE ) :
        print_warn( f'> No \'{CONFIG_FILE}\' found, no branch rules applied.' )

        sys.exit( 0 )
    else :
        rules = load_rules( )
        
        if branch in rules :
            allowed_folders = rules[ branch ]
            allowed_paths = [ os.path.normpath( p ) for p in allowed_folders ]

            for file_path in file_list : 
                if not file_path :
                    continue

                norm_path = os.path.normpath( file_path )
                is_allowed = True if '.' in allowed_paths else any( norm_path.startswith( allowed ) for allowed in allowed_paths )

                if not is_allowed :
                    print_errr( f'> You can\'t commit \'{file_path}\' on branch \'{branch}\'' )
                    print_errr( f'> Only {allowed_folders} are accepted.')
                    print_errr( f'> Edit \'{CONFIG_FILE}\' file if the folder is missing from the path.')
                    sys.exit( 1 )
        else :
            print_warn( f'> Branch \'{branch}\' not found in \'{CONFIG_FILE}\'.' )

'''
   validate_stagging method
   @brief Validate Stagged files. 
'''
def validate_stagging( ) :
    staged_files = get_staged_files( )

    validate_files( staged_files )

'''
	Main entry 
'''
if __name__ == "__main__" :
    args = sys.argv[ 1: ]

    print_message( f'{args}' )
 
    if len( args ) > 0 :
        if args[ 0 ] == '--add-rule' :
            add_rule( args )
        else :
            validate_files( args )
    else :
        validate_stagging( )
