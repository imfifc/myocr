def ai_data_2_raw_data(ai_data):
    if len(ai_data['subjects']) == 0:
        raise AssertionError('INSUFFICIENT_SUBJECTS')
    subject = ai_data['subjects'][0]  # select fist one if multiple are detected

    raw_data = []

    if 'texts' in subject['recognition'] and subject['recognition']['texts']:
        for item in subject['recognition']['texts']:
            raw_data.append([
                item['chars']['content'],
                item['labeled_bbox']['bbox']['left'],
                item['labeled_bbox']['bbox']['top'],
                item['labeled_bbox']['bbox']['right'],
                item['labeled_bbox']['bbox']['bottom'],
                item['labeled_bbox']['label'],
                *item['chars']['probabilities']
            ])

    if 'rotated_texts' in subject['recognition'] and subject['recognition']['rotated_texts']:
        for item in subject['recognition']['rotated_texts']:
            raw_data.append([
                item['chars']['content'],
                item['labeled_bbox']['bbox']['x1'],
                item['labeled_bbox']['bbox']['y1'],
                item['labeled_bbox']['bbox']['x2'],
                item['labeled_bbox']['bbox']['y2'],
                item['labeled_bbox']['bbox']['x3'],
                item['labeled_bbox']['bbox']['y3'],
                item['labeled_bbox']['bbox']['x4'],
                item['labeled_bbox']['bbox']['y4'],
                item['labeled_bbox']['bbox']['angle'],
                item['labeled_bbox']['label'],
                *item['chars']['probabilities']
            ])
    # resize 后的图片大小，-1 说明key不存在
    img_w,img_h =-1,-1
    if ai_data.get('pre_process'):
        if ai_data.get('pre_process').get('image_scale'):
            if ai_data.get('pre_process').get('image_scale').get('width') and \
                    ai_data.get('pre_process').get('image_scale').get('height'):
                img_w,img_h=(ai_data['pre_process']['image_scale']['width'],
                ai_data['pre_process']['image_scale']['height'] )

    return {
        'structuring_data': subject['structuring'].get('data', {}),
        'structuring_meta': subject['structuring'].get('meta', {}),
        'preprocess_result': {
            'scale':[img_w,img_h],
            'roi': [subject['roi']['bbox']['left'], subject['roi']['bbox']['top'],
                    subject['roi']['bbox']['right'], subject['roi']['bbox']['bottom']],
            'orientation': {
                'vote_rotation': subject['orientation']['vote'],
                'executed_rotation': subject['orientation']['execute']
            },
            'small_angle_adjust': subject['post_roi'].get('small_angle_adjust', {}),
            'small_angle_adjust_expand_enabled' : subject['post_roi'].get('expand_enabled',False)
        },
        'raw_data': raw_data
    }
