import json
from file_interface import FileInterface
import logging

class FileProtocol:
    def __init__(self):
        self.fi = FileInterface()

    def proses_string(self, s):
        tokens = s.strip().split()
        logging.warning(f"[PROTOCOL] Command tokens: {tokens[:3]} ... (total {len(tokens)})")
        if not tokens:
            return json.dumps({"status": "ERROR", "message": "Empty command"})

        perintah = tokens[0].upper()
        if perintah == "LIST":
            files = self.fi.list_files()
            return json.dumps({"status": "OK", "data": files})
        elif perintah == "GET":
            if len(tokens) < 2:
                return json.dumps({"status": "ERROR", "message": "filename required"})
            fname = tokens[1]
            filedata = self.fi.get_file(fname)
            if filedata is None:
                return json.dumps({"status": "ERROR", "message": "File not found"})
            return json.dumps({"status": "OK", "data_namafile": fname, "data_file": filedata})
        elif perintah == "UPLOAD":
            if len(tokens) < 3:
                logging.warning("[PROTOCOL] UPLOAD GAGAL: Kurang argumen")
                return json.dumps({"status": "ERROR", "message": "filename and content required"})
            fname = tokens[1]
            content_b64 = " ".join(tokens[2:])
            try:
                self.fi.upload_file(fname, content_b64)
                logging.warning(f"[PROTOCOL] UPLOAD SUKSES: {fname}, size base64: {len(content_b64)}")
                return json.dumps({"status": "OK", "message": "Upload success"})
            except Exception as e:
                logging.exception(f"[PROTOCOL] UPLOAD ERROR: {e}")
                return json.dumps({"status": "ERROR", "message": f"Upload failed: {e}"})
        elif perintah == "DELETE":
            if len(tokens) < 2:
                return json.dumps({"status": "ERROR", "message": "filename required"})
            fname = tokens[1]
            result = self.fi.delete_file(fname)
            if result:
                return json.dumps({"status": "OK", "message": "File deleted"})
            else:
                return json.dumps({"status": "ERROR", "message": "File not found"})
        else:
            return json.dumps({"status": "ERROR", "message": "Unknown command"})