#!/usr/bin/env python3.4


#import json
import binascii

class FalsePositiveException(Exception): pass

class File(object):
    
    signature = b''

    def __init__(self, input_fh, starting_offset):

        self.starting_offset    = starting_offset
        self.size               = ''
        self.data               = ''

        self.intput_fh          = intput_fh
        self.extension          = ''

    '''
    Public methods
    '''

    def save(self):
        '''
        save the data to disk using some filename.
        '''
        pass

    def decode(self):
        '''
        Dump out all data in a nice format, override for each filetype.
        '''
        pass


    '''
    Private Methods
    '''

    def _get_f_size(self):
        # override this for each filetype
        pass


    def _get_f_data(self):
        return self._carve(self.starting_offset,self.size)

    def _carve(self,offset,num_bytes):
        '''
        Carve the specified number of bytes out of the input file at the given offset.
        '''
        try:
            with open(self.input_fh, 'rb') as f:
                f.seek(offset)
                return f.read(num_bytes)
        
        except OSError as err:
            print("[!] Fatal, OSError: {}".format(err))

class LinkFile(File):
    
    signature       = b'\x4C\x00\x00\x00'
    clsid_signature = b'\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46' 

    def __init__(self, input_fh, starting_offset):

        self.clsid_signature    = clsid_signature
        self.extension          = '.lnk'
        self.input_fh           = input_fh
        self.starting_offset    = starting_offset

        self._check_clsid()
        
        self.size               = 4000
        self.data               = self._get_f_data()

    '''
    Private methods
    '''

    def _check_clsid(self):
        '''
        Verify that the file in question has the proper clsid. Raise an exception if not.
        '''

        f_clsid = self._carve(self.starting_offset+4,16)

        if f_clsid != clsid_signature:
            raise FalsePositiveException
        else:
            return f_clsid

class PrefetchFile(File):

    signature = b'\x53\x43\x43\x41'

    def __init__(self, input_fh, starting_offset):

        self.extension          = '.pf'
        self.input_fh           = input_fh

        self._versions          = {
            'xp'        : b'\x11\x00\x00\x00',
            'vista_7'   : b'\x17\x00\x00\x00',
            '8'         : b'\x1A\x00\x00\x00',
            '10'        : b'MAM'
        }

        # In prefetch files, signatures are stored at offset 0x03 in the file.
        self.starting_offset    = starting_offset-4
        self.version            = self._get_f_version()
        self.size               = self._get_f_size()
        self.data               = self._get_f_data()

    def _get_f_size(self):
        '''
        Carve out file size, convert it to big endian, then decimal.
        '''

        size_offset = self.starting_offset + 12
        f_size_le   = self._carve(size_offset,4)
        # flip endianness 
        f_size_be   = int(binascii.hexlify(f_size_le[::-1]),16)

        return f_size_be

    def _get_f_version(self):
        version = self._carve(self.starting_offset,4)

        if version not in self._versions.values():
            raise FalsePositiveException
        else:
            return version

class RawDiskImage(object):

    def __init__(self,input_fh):

        self.input_fh               = input_fh
        self.supported_filetypes    = self._get_supported_files()

    '''
    Public Methods
    '''

    def find(self,ftype):
        '''
        maybe find based on a certain list of supported files?
        '''

        results = list()

        if ftype not in self.supported_filetypes.keys():
            raise Exception("[!] {} is not a supported filetype, please select one of the following: {}".format(ftype,self.supported_filetypes.keys()))
        else:
            signature = self.supported_filetypes[ftype].signature
            class_ref = self.supported_filetypes[ftype]

        try:
            with open(self.input_fh, 'rb') as f:

                # record the end of the file, the set the pointer back to the beginning
                file_size = f.seek(0,2)
                f.seek(0,0)

                chunk = f.read(4)

                while f.tell() < file_size:

                    # since the reference point is at the end of the 4 bytes, we must subtract 4 bytes to get the starting offset of our signature.
                    signature_offset = f.tell()-4

                    if chunk == signature:
                        '''
                        if we have a match, create an object and add it to a list or something.
                        '''

                        try:
                            results.append(class_ref(self.input_fh,signature_offset))
                            print("[+] Found a {} at offset {}".format(class_ref.__name__,signature_offset))
                        except FalsePositiveException:
                            pass

                    # seek the pointer back 3 bytes, so that we wind up iterating over the file one byte at a time.
                    f.seek(-3,1)
                    chunk = f.read(4)

        except OSError as err:
            print("[!] Fatal, OSError: {}".format(err))

        return results

        

    '''
    Private Methods
    '''

    def _get_supported_files(self):
        '''
        Find all defined subclasses of File and get each subclass' file signature.
        Return a dict with the following structure.

        { subclass name : subclass_reference }
        '''

        return { subclass.__name__ : subclass for subclass in File.__subclasses__()}