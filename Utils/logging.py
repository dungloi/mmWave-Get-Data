import logging
import sys
import time
import colorlog

'''
 %(levelno)s:     打印日志级别的数值
 %(levelname)s:   打印日志级别名称
 %(pathname)s:    打印当前执行程序的路径，其实就是sys.argv[0]
 %(filename)s:    打印当前执行程序名
 %(funcName)s:    打印日志的当前函数
 %(lineno)d:      打印日志的当前行号
 %(asctime)s:     打印日志的时间
 %(thread)d:      打印线程ID
 %(threadName)s:  打印线程名称
 %(process)d:     打印进程ID
 %(message)s:     打印日志信息
'''
log_colors_config = {
    'DEBUG': 'white',  # cyan white
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}

DEBUG_ON = 0

class Logger(object):
    
    def __init__(self, logger, log_path="Log"):
        self.logger = logging.getLogger(name=logger)
        if DEBUG_ON:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.NOTSET)
        self.logPath = log_path

        # create log file
        curTime = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(time.time()))
        log_name = self.logPath + "/" +logger + "_" + curTime + ".log"

        if not self.logger.handlers:
            console_handel = logging.StreamHandler(sys.stdout)
            console_handel.setLevel(logging.DEBUG)
            console_formatter = colorlog.ColoredFormatter(
                fmt='%(log_color)s[%(asctime)s.%(msecs)03d] pid: %(thread)s %(filename)s -> %(funcName)s line:%(lineno)d [%(levelname)s] : %(message)s',
                datefmt='%Y-%m-%d  %H:%M:%S',
                log_colors=log_colors_config)
            console_handel.setFormatter(console_formatter)
            self.logger.addHandler(console_handel)

            file_handler = logging.FileHandler(filename=log_name, mode='a', encoding='utf8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                fmt='[%(asctime)s.%(msecs)03d] pid: %(thread)s %(filename)s -> %(funcName)s line:%(lineno)d [%(levelname)s] : %(message)s',
                datefmt='%Y-%m-%d  %H:%M:%S')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)


if __name__ == '__main__':
    log = Logger("LOGTEST").logger
    log.debug("debug")
    log.info("info")
    log.waring("warning")
    log.error("error")
    log.critical("critical")



