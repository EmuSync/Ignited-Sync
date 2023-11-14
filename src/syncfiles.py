#from datetime import datetime
import os, shutil

def compareFilesStamp(localFile, remoteFile, mode: int = 1): # file paths. mode 1 is local sync files. mode 2 is local file time and input remote time.
    remoteExist = False

    if os.path.exists(localFile):
        localFileTime = os.path.getmtime(localFile)
        print("file1: ", os.path.getmtime(localFile)," ", localFile)
    else:
        localFileTime = 0

    if not isinstance(remoteFile, float) and not isinstance(remoteFile, int) and os.path.exists(remoteFile) and mode == 1:
        remoteFileTime = os.path.getmtime(remoteFile)
        print("file2: ", os.path.getmtime(remoteFile)," ", remoteFile)
    elif mode == 2:
        
        remoteFileTime = float(remoteFile)
    else:
        remoteFileTime = 0

    if isinstance(remoteFile, str):
        if os.path.exists(remoteFile):
            remoteExist = True

    if localFileTime > remoteFileTime or os.path.exists(localFile) is False:
        print(localFileTime," ",remoteFileTime," ", remoteExist)
        choice = input("Upload File? y/n: ")

        if choice == "y":
            if mode == 1:
                print("Transfering: ", localFile)
                shutil.copy2(localFile, remoteFile)
                print("Transfer Complete")
                return 2
            elif mode == 2:
                print("Uploading: ")
                return 2
        
        elif choice == "n":
            print("Declined")
            return 0
        
        else:
            print("No input")
            return 0
        
    elif localFileTime < remoteFileTime or os.path.exists(localFile) is False:
        if mode == 1:
            print("Transfering: ", remoteFile)
            shutil.copy2(remoteFile, localFile)
            print("Transfer Complete")
            return 1
        elif mode == 2:
            print("Downloading: ")
            return 1
    
    else:
        print("Match")
        return 0

sysFile = "/run/media/deck/5b860f23-1efd-4ba5-8336-603c1dde8b94/git/Delta-Reversing/sync/local/README.md"
#serverFile = "/run/media/deck/5b860f23-1efd-4ba5-8336-603c1dde8b94/git/Delta-Reversing/sync/remote/README.md"
serverFile = 1693111151.583715

compareResults = compareFilesStamp(sysFile, serverFile,2)
