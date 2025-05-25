import os
import base64

class FileInterface:
    def __init__(self, base_path="."):
        self.base_path = base_path

    def list_files(self):
        return [f for f in os.listdir(self.base_path) if os.path.isfile(os.path.join(self.base_path, f))]

    def get_file(self, filename):
        path = os.path.join(self.base_path, filename)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        return content

    def upload_file(self, filename, content_b64):
        # Tambahkan padding jika perlu sebelum decode
        missing_padding = len(content_b64) % 4
        if missing_padding:
            content_b64 += '=' * (4 - missing_padding)
        path = os.path.join(self.base_path, filename)
        with open(path, "wb") as f:
            f.write(base64.b64decode(content_b64))
        return True

    def delete_file(self, filename):
        path = os.path.join(self.base_path, filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False