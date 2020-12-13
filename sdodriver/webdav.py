from webdav3.client import Client


class Cloud(Client):
    """
    Methods using webdav protocol for fast getting information and creating paths
    """
    def __init__(self, login, password, token):
        opts = {
            'webdav_hostname': token,
            'webdav_login': login,
            'webdav_password': password,
        }
        super().__init__(opts)

    def free_space(self):
        """
        Account free space calculation

        :return: print volume in gigabytes. If it is less than 10GB, then number will be red
        """
        fs = float(self.free())
        for i in range(3):
            fs /= 1024
        color = '\033[31m' if fs < 10 else '\033[32m'
        print(f'Free space in your cloud [cloud.rgsu.net]: {color}{fs:.1f}\033[0m GB')

    def check_path(self, p_dir: str):
        """
        Checks if directory exists, if not then create such path

        :param p_dir: directory path to check
        :return: print info if directory was created
        """
        if not self.check(p_dir):
            self.mkdir(p_dir)
            print(f'Directory [\033[36m{p_dir}\033[0m] created.')
