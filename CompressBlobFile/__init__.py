import logging
import sys
import locale
import tempfile
import os
import subprocess
import ntpath
import errno
import azure.functions as func


def main(rawblob: func.InputStream, optimizedblob: func.Out[func.InputStream], context: func.Context) -> None:
    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {rawblob.name}\n"
                 f"Blob Size: {rawblob.length} bytes")

     #context.function_directory
    name = ntpath.basename(rawblob.name)
    #root, ext = os.path.splitext(name)

    temp = tempfile.gettempdir()
    filename = os.path.join(temp, name)
    outfilename = os.path.join(temp, "out" + name)

    logging.info(f"Temp File {filename}")
    logging.info(f"Temp Out File {outfilename}")
  
    
    with open(filename, 'wb') as tmpfile:
        tmpfile.write(rawblob.read())

    if(name.endswith(".csv")):
        optimizedblob.set(rawblob.read())
        with open(filename, 'rb') as outfilecsv:
            logging.info("Writing csv file out to Blob")
            optimizedblob.set(outfilecsv.read())
            logging.info(f"Copy file to directory: {name}")
        return

    #apt-get -y install ghostscript
    try:
        subprocess.call(['gs'])
    except OSError as e:
        if e.errno == errno.ENOENT:
            #Handle Process not found
            #REMOVE THIS COMMAND WHEN USING DOCKER FILE/CONTAINER
            #DOCKERFILE WILL INSTALL GHOSTSCRIPT
            logging.info("Installing Ghostscript")
            command = subprocess.run(["apt-get", "-y", "install", "ghostscript"], check=True)
            logging.debug(f"The exit code for installing Ghostscript: {command.returncode}")

            #Command was executed and the return code was not successful(0) 
            if command.returncode != 0:
                logging.error("Unable to install Ghostscript. Exiting function app...")
                return
        else:
            logging.error("Error with installing Ghostscript. Exiting function app...")
            return 
    
    
    try:
        logging.info("Begin compressing PDF...")
        #initial_size = os.path.getsize(filename)
        subprocess.call(['gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                        '-dPDFSETTINGS=/ebook',
                        '-dNOPAUSE', '-dQUIET', '-dBATCH',
                        '-sOutputFile='+ outfilename,
                         filename]
        )
    except OSError as e:
        logging.error(f"Error code when executing Ghostscript program: {e.errno}")
        return

    logging.info("Compression Completed")

    logging.info(f"Temp file Location {outfilename}")
    logging.info("***-----------Testing writing out to Blob-------------***")
    with open(outfilename, 'rb') as outfile:
        logging.info("Writing out to Blob")
        optimizedblob.set(outfile.read())
        logging.info(f"Successful in Compression with file: {outfilename}")
