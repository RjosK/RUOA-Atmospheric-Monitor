import logging
import sys

def get_logger(name='LAIDEA_Pipeline'):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # Optional: File handler
        # fh = logging.FileHandler('pipeline.log')
        # fh.setFormatter(formatter)
        # logger.addHandler(fh)
        
    return logger
