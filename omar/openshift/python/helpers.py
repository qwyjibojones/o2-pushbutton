import logging


def report_status(name, process):
    output, error = process.communicate()
    return_code = process.returncode
    if return_code == 0:
        logging.info('%s: Success!' % name)
        if len(output) > 0:
            logging.debug('stdout: %s' % output)
        if len(error) > 0:
            logging.debug('stderr: %s' % error)
    else:
        logging.error('!!!!! Failure with object: %s !!!!!' % name)
        if len(output) > 0:
            logging.warning('stdout: %s' % output)
        if len(error) > 0:
            logging.warning('stderr: %s' % error)

    return return_code
