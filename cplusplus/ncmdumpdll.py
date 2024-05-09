import ctypes
import os

class NcmdumpDll:
    def __init__(self, file_name):
        dll_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "libncmdump.dll"))
        self.dll = ctypes.CDLL(dll_path)
        
        # Define function prototypes
        self.dll.CreateNeteaseCrypt.argtypes = [ctypes.c_char_p]
        self.dll.CreateNeteaseCrypt.restype = ctypes.c_void_p
        
        self.dll.Dump.argtypes = [ctypes.c_void_p]
        self.dll.Dump.restype = ctypes.c_int
        
        self.dll.FixMetadata.argtypes = [ctypes.c_void_p]
        self.dll.FixMetadata.restype = None
        
        self.dll.DestroyNeteaseCrypt.argtypes = [ctypes.c_void_p]
        self.dll.DestroyNeteaseCrypt.restype = None
        
        # Convert file name to bytes
        file_bytes = file_name.encode('utf-8')
        
        # Allocate memory and copy file name bytes
        input_ptr = ctypes.create_string_buffer(file_bytes)
        
        # Create NeteaseCrypt instance
        self.netease_crypt = self.dll.CreateNeteaseCrypt(input_ptr)
    
    def dump(self):
        return self.dll.Dump(self.netease_crypt)
    
    def fix_metadata(self):
        self.dll.FixMetadata(self.netease_crypt)
    
    def destroy(self):
        self.dll.DestroyNeteaseCrypt(self.netease_crypt)

    def process_file(self):
        self.dump()
        self.fix_metadata()
        self.destroy()

if __name__ == "__main__":
    # 文件名
    file_path = "YOASOBI.ncm"
    # 创建 NeteaseCrypt 类的实例
    netease_crypt = NcmdumpDll(file_path)
    # 启动转换过程
    netease_crypt.process_file()
