import multiprocessing
import traceback
import argparse
import string
import stat
import sys
import os


# Generator functions for creating all strings of length k given a list of values
# https://www.geeksforgeeks.org/print-all-combinations-of-given-length/
def getAllKLength(values, k):
    yield from getAllKLengthRec(values, "", len(values), k)


def getAllKLengthRec(values, prefix, n, k):

    # The main recursive method
    # to print all possible
    # strings of length k

    # Base case: k is 0,
    # print prefix
    if (k == 0) :
        yield prefix
        return

    # One by one add all characters
    # from values and recursively
    # call for k equals to k-1
    for i in range(n):

        # Next character of input added
        newPrefix = prefix + values[i]

        # k is decreased, because
        # we have added a new character
        yield from getAllKLengthRec(values, newPrefix, n, k - 1)


# Different overwrite patterns in Gutmann's method, -1 represents random
patterns = [[-1, 'random']]*4 + [
            [b'\x55'*3, '55'*3],          # 5
            [b'\xaa'*3, 'aa'*3],          # 6
            [b'\x92\x49\x24', '924924'],  # 7
            [b'\x49\x24\x92', '492492'],  # 8
            [b'\x24\x92\x49', '249249'],  # 9
            [b'\x00'*3, '00'*3],          # 10
            [b'\x11'*3, '11'*3],          # 11
            [b'\x22'*3, '22'*3],          # 12
            [b'\x33'*3, '33'*3],          # 13
            [b'\x44'*3, '44'*3],          # 14
            [b'\x55'*3, '55'*3],          # 15
            [b'\x66'*3, '66'*3],          # 16
            [b'\x77'*3, '77'*3],          # 17
            [b'\x88'*3, '88'*3],          # 18
            [b'\x99'*3, '99'*3],          # 19
            [b'\xaa'*3, 'aa'*3],          # 20
            [b'\xbb'*3, 'bb'*3],          # 21
            [b'\xcc'*3, 'cc'*3],          # 22
            [b'\xdd'*3, 'dd'*3],          # 23
            [b'\xee'*3, 'ee'*3],          # 24
            [b'\xff'*3, 'ff'*3],          # 25
            [b'\x92\x49\x24', '924924'],  # 26
            [b'\x49\x24\x92', '492492'],  # 27
            [b'\x24\x92\x49', '249249'],  # 28
            [b'\x6d\xb6\xdb', '6db6db'],  # 29
            [b'\xb6\xdb\x6d', 'b6db6d'],  # 30
            [b'\xdb\x6d\xb6', 'db6db6']   # 31
        ] + [[-1, 'random']]*4


def verboseprint(msg, verbose):
    '''
    Prints a message when verbose is True

        Parameters:
            msg (str):       message to be printed
            verbose (bool):  prints only if true
    '''
    if verbose:
        print('pyshred: ' + msg)


def force_permissions(file, verbose):
    '''
    Changes file permissions to allow modifications

        Parameters:
            file (str):      path of file
            verbose (bool):  prints progress when True
    '''

    verboseprint("Changing file permissions: '" + file + "'", verbose)

    # Windows case
    if sys.platform == 'win32':
        val = os.system('powershell -command "icacls \'' + file + '\' /grant:r ${env:username}:M /remove:d ${env:username} | Out-Null; if(!$?){exit 1}"')
        if val != 0:
            print("Could not change file permissions: '" + file + "'")
            return
    
    # Linux and macOs case. For Windows this clears
    # the read-only bit
    try:
        os.chmod(file, stat.S_IWUSR|stat.S_IRUSR)
    except:
        traceback.print_exc()
        print("Could not change file permissions: '" + file + "'")
        return
    
    verboseprint("File permissions successfully changed: '" + file + "'", verbose)


def delete(file, recursive, verbose, force, changed):
    '''
    Remove a file or directory

    Name of file is replaced with another available name
    of the same length containing string.digits or 
    string.ascii_letters symbols. The file is renamed
    multiple times each with a shorter file name until
    the name is of lenght 1. The file is deleted afterwards.
    If no available name for a particular lenght is found
    this function's generator raises a StopIteration
    exception.

        Parameters:
            file (str):                 path of file to be deleted
            recursive (bool):           remove directories recursively
            verbose (bool):             prints progress when True 
            force (bool):               when True, call force_permissions(file) if needed
            changed (bool):             When True, indicates that force_permissions(file) has already been called
    '''

    # Delete folder contents first
    abs_path = os.path.abspath(file)
    if os.path.isdir(file):
        name = os.path.basename(file)
        if name == '':
            # Windows path fix
            name = os.path.basename(os.path.dirname(file))
        if name == '':
            print("Deleting error, could not get file base name for path: '" + file + "'")
            return
        if recursive:
            files = []
            try:
                files = os.listdir(file)
            except PermissionError:
                if force:
                    force_permissions(file , verbose)
                    try:
                        files = os.listdir(file)
                    except:
                        traceback.print_exc()
                        return
                else:
                    traceback.print_exc()
                    return
            except:
                traceback.print_exc()
                return
            for f in files:
                delete(os.path.join(file, f), recursive, verbose, force, False)
        else:
            print("Attempted to delete directory without the recursive flag: '" + file + "'")
            sys.exit(-1)
    elif os.path.isfile(file):
        name = os.path.basename(file)
    else:
        print("Attempted to delete invalid file: '" + file + "'")
        return

    # Get an available name of current length using a generator
    chars = string.digits + string.ascii_letters
    gen = getAllKLength(chars, len(name))
    curr = next(gen)
    while os.path.isdir(curr) or os.path.isfile(curr):
        curr = next(gen)


    # Main deletion part
    try:
        # Opening the file in 'r+' mode is a check that avoids the 
        # case of having a file with write only permissions, 
        # shredding it, and then deleting it. In this case the shred 
        # would fail because 'r+' mode is needed but the
        # deletion would be successful. This makes the contents
        # of the file potentially recoverable.
        if os.path.isfile(abs_path):
            with open(abs_path, 'r+'):
                pass

        # Raise an exception if a nonempty folder is attempted to
        # be deleted
        if os.path.isdir(abs_path) and len(os.listdir(abs_path)) != 0:
            e = Exception("Attempted to delete a non-empty directory: '" + abs_path + "'")
            raise e

        # Removing process starts
        verboseprint(file + ': removing', verbose)

        # Initial rename
        os.rename(abs_path, curr)

        verboseprint(file + ': renamed to ' + curr, verbose)

        # Main deletion loop
        while(len(curr) > 1):

            # Find new available name
            old = curr
            gen = getAllKLength(chars, len(curr)-1)
            curr = next(gen)
            while os.path.isdir(curr) or os.path.isfile(curr):
                curr = next(gen)

            # Rename
            os.rename(old, curr)
            verboseprint(old + ': renamed to ' + curr, verbose)
        
        # Remove file or directory
        if os.path.isdir(curr):
            os.rmdir(curr)
        else:
            os.remove(curr)
        verboseprint(file + ': removed', verbose)
    
    except PermissionError:
        if force and not changed:
            try:
                # Change permissions
                force_permissions(file, verbose)

                # Try to delete again with new permissions
                delete(file, recursive, verbose, force, True)
            except:
                traceback.print_exc()
        else:
            traceback.print_exc()
    except:
        traceback.print_exc()


def shred_helper(file, buffer, N, zero, sem, verbose, force, changed):
    '''
    Helper function for shred(). Meant to be called
    by shred() through a newly spawn process.
    '''
    
    length = os.path.getsize(file)
    try:
        with open(file, "br+", buffering=buffer) as f:
            for i in range(N):
                pattern = patterns[i % len(patterns)][0]
                # Put pointer at the beggining of file
                f.seek(0)
                # Random data case
                if pattern == -1:
                    f.write(os.urandom(length))
                # Pattern case
                else:
                    # Repeats pattern
                    # https://stackoverflow.com/a/3391106/9477227
                    f.write((pattern * (length//len(pattern) + 1))[:length])
                # Flush file
                f.flush()
                verboseprint(file+': pass: '+str(i+1)+'/'+str(N)+' ('+patterns[i%len(patterns)][1]+')...', verbose)
            # Hide shred
            if zero:
                f.seek(0)
                f.write(b'\x00'*length)
                verboseprint(file+': pass: '+str(i+1+1)+'/'+str(N+1)+' ('+'00'*3+')...', verbose)
            f.close()
    
    except PermissionError:
        if force and not changed:
            try:
                # Change permissions
                force_permissions(file, verbose)

                # Try to shred again with new permissions
                shred_helper(file, buffer, N, zero, sem, verbose, force, True)
            except:
                traceback.print_exc()
        else:
            traceback.print_exc()
    except:
        traceback.print_exc()

    # Release semaphore
    if not changed:
        sem.release()


def shred(file, buffer, N, recursive, zero, processes, sem, verbose, force):
    '''
    Overwrites a file using the Gutmann's method.
    WARNING: has not been tested with large files
    WARNING: parameters are validated in main(), not here
    WARNING: does nothing to files that are not directories or regular files

        Parameters:
            file (str):                              path of file to be shreded, assumes it's not a directory
            buffer (int):                            buffer size in bytes
            N (int):                                 number of overwrites (loops over Gutmann's method passes)
            recursive (bool):                        shred directories and their contents recursively
            zero (bool):                             add a final overwrite with zeros to hide shredding
            processes (list):                        list containing all processes
            sem (multiprocessing.BoundedSemaphore):  multiprocess semaphore
            verbose (bool):                          print progress when True
            force (bool):                            when True, call force_permissions(file) if needed                            
    '''
    if N > 0:
        # Regular file case
        if os.path.isfile(file):
            # Important part that multiple processes need to handle
            p = multiprocessing.Process(target=shred_helper, args=(file, buffer, N, zero, sem, verbose, force, False))
            processes.append(p)
            sem.acquire()
            p.start()
        # Directory case. Applies shred recursively
        elif os.path.isdir(file):
            if recursive:
                files = []
                try:
                    files = os.listdir(file)
                except PermissionError:
                    if force:
                        force_permissions(file, verbose)
                        try:
                            files = os.listdir(file)
                        except:
                            traceback.print_exc()
                    else:
                        traceback.print_exc()
                except:
                    traceback.print_exc()
                # Shred each file inside directory
                for f in files:
                    shred(os.path.join(file, f), buffer, N, recursive, zero, processes, sem, verbose, force)
            else:
                print("Directory specified without the recursive flag: '" + file + "'")
                sys.exit(-1)
        else:
            print("Attempted to shred invalid file: '" + file + "'")


if __name__=='__main__':
    '''
    Main execution function
    '''
    # Parse Arguments
    parser = argparse.ArgumentParser(description="Simple, recursive, multiprocess, file shredder implementing Gutmann's 35 pass method. https://en.wikipedia.org/wiki/Gutmann_method")
    parser.add_argument('-f','--force', help='if necessary, change file permissions to allow reading and writing', action='store_true')
    parser.add_argument('-r', '-R', '--recursive', help='shred the contents of directories recursively', action='store_true')
    parser.add_argument('-u', '--unlink', help='remove files after overwriting', action='store_true')
    parser.add_argument('-v', '--verbose', help='show progress', action='store_true')
    parser.add_argument('-z','--zero', help='add a final overwrite with zeros to hide shredding', action='store_true')
    parser.add_argument('-B', default=-1, type=int, nargs='?', help='open files with a buffer of approximately B bytes (default: io.DEFAULT_BUFFER_SIZE)', metavar='buffer size')
    parser.add_argument('-N', default=35, type=int, nargs='?', help="number of passes, program loops through the Gutmann method's passes until N overwrites have been made (default: 35)", metavar='passes')
    parser.add_argument('-P', default=1, type=int, nargs='?', help='limit to P processes shredding at a time, one per file (default: 1)', metavar='processes')
    parser.add_argument('files', type=str, nargs='+', help='files to be shredded', metavar='files')
    args = parser.parse_args()

    # Clean and validate arguments
    if args.N < 0:
        raise argparse.ArgumentTypeError('Number of passes must be greater than or equal to 0')
    if args.P < 1:
        raise argparse.ArgumentTypeError('Number of processes must be greater than 0')
    if args.B < 2 and args.B != -1:
        raise argparse.ArgumentTypeError('Buffer size must be greater than 1 byte')
    args.files = list(dict.fromkeys(args.files))

    # Multiprocess variables
    processes = []
    lock = multiprocessing.Lock()
    sem = multiprocessing.BoundedSemaphore(args.P)

    # Shred files
    for file in args.files:
        shred(file, args.B, args.N, args.recursive, args.zero, processes, sem, args.verbose, args.force)

    # Wait for files to be shreded
    for p in processes:
        p.join()

    # Shred directories if needed
    if args.unlink:
        for file in args.files:
            delete(file, args.recursive, args.verbose, args.force, False)
