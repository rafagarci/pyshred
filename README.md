# pyshred

Simple, recursive, multiprocess, file shredder implementing [Gutmann's 35 pass method](https://en.wikipedia.org/wiki/Gutmann_method).

## Usage

```text
usage: pyshred.py [-h] [-f] [-r] [-u] [-v] [-z] [-B [buffer size]] [-N [passes]] [-P [processes]] files [files ...]

positional arguments:
  files                files to be shredded

optional arguments:
  -h, --help           show this help message and exit
  -f, --force          if necessary, change file permissions to allow reading and writing
  -r, -R, --recursive  shred the contents of directories recursively
  -u, --unlink         remove files after overwriting
  -v, --verbose        show progress
  -z, --zero           add a final overwrite with zeros to hide shredding
  -B [buffer size]     open files with a buffer of approximately B bytes (default: io.DEFAULT_BUFFER_SIZE)
  -N [passes]          number of passes, program loops through the Gutmann method's passes until N overwrites have been made (default: 35)
  -P [processes]       limit to P processes shredding at a time, one per file (default: 1)
```

## CLI

You can run the script directly from a command-line as follows

PowerShell:

```powershell
(Invoke-WebRequest https://raw.githubusercontent.com/rafagarci/pyshred/main/pyshred.py).content | Out-File -Encoding utf8 pyshred.py; if($?){python3 .\pyshred.py <arguments here>; python3 .\pyshred.py -zu .\pyshred.py}
```

Unix:

```bash
if curl -sSfo pyshred.py https://raw.githubusercontent.com/rafagarci/pyshred/main/pyshred.py; then python3 pyshred.py <arguments here>; python3 pyshred.py -zu pyshred.py; fi
```

Note that the above downloads `pyshred.py` into the running directory, uses it to shred the desired files, and finally shreds and unlinks `pyshred.py`.

## Caution

Just like Unix's [`shred`](https://en.wikipedia.org/wiki/Shred_(Unix)#:~:text=shred%20is%20a%20command%20on,part%20of%20GNU%20Core%20Utilities.) command, this script relies on a very important assumption: that the file system overwrites data in place. This is the traditional way to  do things, but many modern file system designs do not satisfy this assumption.

See the **caution** section [here](https://linux.die.net/man/1/shred) for more details.

## Notes

### Too many open files

Script might fail if there are many files being shred at once since the OS often limits the number of files one can have open at a given time. See the following pages for a macOS and Linux fix:

- [Page 1](https://stackoverflow.com/questions/16526783/python-subprocess-too-many-open-files)

- [Page 2](http://woshub.com/too-many-open-files-error-linux/)

### Functionality

The `force` option was developed with Linux, macOS, and Windows in mind. This script heavily relies on `os` module's operations and has not been tested on other OS.

### TODOs

- Do rigorous testing

## Requirements

- Python 3.2 or later

## License

GNU GPLv3 © Rafael García
