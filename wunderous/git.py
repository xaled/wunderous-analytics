import requests
import logging
from time import time
from wunderous.config import config

logger = logging.getLogger(__name__)


def get_git_dates():
    lines_dates = list()
    try:
        resp = requests.get(config['rewards']['git']['url'])
        lines = resp.text.split('\n')
        for l in lines:
            try:
                if "data-count" in l and not 'data-count="0"' in l:
                    lines_dates.append(l.split()[-1].split('"')[1])
            except:
                logger.error("Error while parsing git date line: %s", l, exc_info=True)
        # [l.split()[-1].split('"')[1] for l in lines if "data-count" in l and not 'data-count="0"' in l]
    except:
        logger.error("Error while getting git dates", exc_info=True)
    return lines_dates