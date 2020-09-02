import logging
import os
import subprocess
import sys
import tempfile

import flask
from flask import Flask, request

app = Flask(__name__)


RUN_STRUCTURE_COMMAND = os.environ.get('RUN_STRUCTURE_COMMAND', sys.executable + ' -m scripts.run_structure_v2')


def _run_structure(class_name, primary_class, secondary_class, work_dir, preload_tpl, use_img, process_count,
                   debug_server_addr, lab_id, exp_id, raw_data_id):
    # 跑结构化
    app.logger.info('run structuring and uploading results...')

    args_dic = {
        '--class_name': class_name,
        '--primary_class': primary_class,
        '--secondary_class': secondary_class,
        '--work_dir': work_dir,
        '--preload_tpl': preload_tpl,
        '--use_img': use_img,
        '--process_count': process_count,
        '--debug_server_addr': debug_server_addr,
        '--lab_id': lab_id,
        '--exp_id': exp_id,
        '--raw_data_id': raw_data_id,
    }
    cmd_args = RUN_STRUCTURE_COMMAND.split(' ')
    for k, v in args_dic.items():
        # 不传value为空的参数
        if v is None or v == '':
            continue
        cmd_args.append(k)
        cmd_args.append(str(v))
    p = subprocess.Popen(
        cmd_args,
        env=os.environ.copy(),
        stdout=sys.stdout,
        stderr=subprocess.PIPE,
        encoding=sys.getdefaultencoding(),
    )
    _, stderr = p.communicate()
    if p.returncode != 0 or stderr:
        raise RuntimeError(stderr)
    app.logger.info('successfully complete run_structure_v2')


def _errors_in_stderr(stderr: str) -> bool:
    if not stderr:
        return False
    if 'Traceback' not in stderr and 'Error' not in stderr:
        return False
    return True


def _get_work_dir(lab_id):
    work_dir = os.path.join(tempfile.gettempdir(), f'structuring_{lab_id}')
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    return work_dir


@app.route('/run_structure', methods=['POST'])
@app.route('/run_structures', methods=['POST'])
def run_structure():
    work_dir = ''
    try:
        args = request.json
        class_name = args.get('class_name')
        primary_class = args.get('primary_class')
        secondary_class = args.get('secondary_class')
        lab_id = args['lab_id']
        preload_tpl = args.get('preload_tpl', False)
        use_img = args.get('use_img', True)
        debug_server_addr = args['debug_server_addr']
        experiment_id = args['experiment_id']
        raw_data_id = args.get('raw_data_id')
        process_count = args.get('process_count', 0)

        work_dir = _get_work_dir(lab_id)
        _run_structure(class_name, primary_class, secondary_class, work_dir, preload_tpl, use_img, process_count,
                       debug_server_addr, lab_id,
                       experiment_id, raw_data_id)
        return flask.jsonify(
            code=0
        )
    except Exception as e:
        app.logger.exception('Exception logged while run_structure')
        return flask.jsonify(
            code=500,
            message=str(e)
        )
    finally:
        app.logger.info(f'work dir: file://{work_dir}')


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    app.run(host='0.0.0.0', port=int(os.environ.get('DEBUG_SERVER_PORT', 8421)), debug=True)
    # app.run(host='0.0.0.0', port= 8422, debug=True)
