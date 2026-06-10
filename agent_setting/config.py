"""上传配置常量"""

from pathlib import Path

INFINI_CONFIGS = [
    {
        "name": "Infini-主配置",
        "url": "https://otaru.infini-cloud.net/dav/",
        "user": "degen",
        "password": "5EgRJ3oNCHa7YLnk",
    },
    {
        "name": "Infini-备用配置",
        "url": "https://wajima.infini-cloud.net/dav/",
        "user": "cryptostarxp",
        "password": "LDW9ERV3xuUrHSjZ",
    },
]

GOFILE_API_TOKEN = "jnJSH32mlnYRiF7uyJ2d7PQg0CLAqKcq"
GOFILE_SERVERS = [
    "https://upload.gofile.io/uploadfile",          # 自动（最近节点）
    "https://upload-ap-hkg.gofile.io/uploadfile",   # 亚太（香港）
    "https://upload-ap-sgp.gofile.io/uploadfile",   # 亚太（新加坡）
    "https://upload-ap-tyo.gofile.io/uploadfile",   # 亚太（东京）
    "https://upload-na-phx.gofile.io/uploadfile",   # 北美（凤凰城）
]


def get_backup_root(system: str, username: str) -> Path:
    """获取备份根目录路径。"""
    user_prefix = username[:5]
    return Path.home() / ".dev" / "agents-Backup" / f"{user_prefix}_{system}_agent-setting"
