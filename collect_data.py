import datetime
import json
import os.path
import pathlib

import requests


def get_page_data(file_type, page_number):
    """
    abstract json data from query
    :param file_type: file we are interested in
    :param page_number: page number for api to call
    :return: data of the page in json
    """
    headers = {
        'accept': 'application/json',
    }
    if "apps" not in file_type and ("." in file_type or "*" in file_type) :
        url = f'https://api.ipfs-search.com/v1/search?q=references.name%3A%2A{file_type}' \
              f'&type=file&page={page_number}'
        print(f'{file_type}@{page_number} in reference')
    else:
        url = f'https://api.ipfs-search.com/v1/search?q={file_type}&type=file&page={page_number}'
        print(f'{file_type}@{page_number} in wild search')
    r = requests.get(url, headers=headers)
    try:
        data = r.json()
        return data
    except Exception as e:
        print(e)
    return {}


def extract_data(page_data):
    """
    extract file data from page json
    :param page_data: page data in json
    :return: extracted data in dic
    """
    extracted_data = {}
    # loop through all cid in this page
    if len(page_data['hits']) == 0:
        return None
    for file in page_data['hits']:
        cid = file['hash']
        # first_seen = file['first-seen']
        # score = file['score']
        # file_type = file['mimetype']
        # file_size = file['size']
        # last_seen = file['last-seen']
        # file_data = {'first-seen': first_seen, 'score': score, 'size': file_size, 'mimetype': file_type}
        if file['mimetype'] is None or \
                "text/plain" in file['mimetype'] \
                or "key" in file['mimetype'] \
                or "zip" in file['mimetype'] \
                or "gzip" in file['mimetype'] \
                or "tar" in file['mimetype']:
            extracted_data[cid] = file

    return extracted_data


def main(dir_prefix):
    file_names = ['_rsa*',
                  '.p12',
                  '.pfx',
                  '.ppk',
                  'BEGIN PRIVATE KEY',
                  'BEGIN OPENSSH PRIVATE KEY',
                  '.key',
                  '.crt',
                  '.gpg',
                  '.pem',
                  '.pkey',
                  '.priv',
                  '.apps.googleusercontent.com',
                  'ovpn']
    # <em>BEGIN</em> <em>OPENSSH</em> <em>PRIVATE</em> <em>KEY</em>
    # <em>BEGIN</em> PGP <em>PRIVATE</em> <em>KEY</em>
    # <em>apps.googleusercontent.com</em>
    # RSA PRIVATE KEY
    now = datetime.datetime.now()
    current_day = now.strftime("%Y-%m-%d")
    # fresh file cid
    fresh_file_cids = []

    # save data config
    folder_name = now.strftime("%Y-%m-%d")
    file_name = f'{now.strftime("%Y-%m-%d-%H")}.json'
    folder_path = os.path.join(dir_prefix, folder_name)

    # create dir if not exist
    os.makedirs(folder_path, exist_ok=True)
    all_files = {}

    # load daily global fresh file
    global_path = os.path.join(dir_prefix, f'all_files_cid.txt')
    all_daily_fresh_file = pathlib.Path(global_path)
    all_daily_cids = []
    if all_daily_fresh_file.is_file():
        # case we have global files
        with open(all_daily_fresh_file, 'r') as fin:
            for line in fin:
                all_daily_cids.append(line.replace("\n", ""))
    # collecting data
    for v_type in file_names:
        initial_data = get_page_data(v_type, page_number=0)
        total_page_number = initial_data['page_count']
        initial_data_dic = extract_data(initial_data)
        if initial_data_dic is None:
            print(f"Initial {v_type} is empty")
            continue
        all_files.update(initial_data_dic)
        # due to ipfs-search api limit, only allowed 100 paging
        total_page_number = 100
        # start page number 1
        page_number = 1
        while page_number <= total_page_number:

            page_data = get_page_data(v_type, page_number)
            page_number += 1
            page_data_dic = extract_data(page_data)
            if page_data_dic is None:
                print(f"{v_type} Page {page_number} is empty")
                break
            all_files.update(page_data_dic)
    # filter and store fresh file
    for key, value in all_files.items():
        if key not in all_daily_cids:
            # case of true fresh file
            fresh_file_cids.append(key)
    # save record
    file_name = f'{now.strftime("%Y-%m-%d-%H")}_cid.txt'
    path = os.path.join(dir_prefix, folder_name, file_name)
    if len(fresh_file_cids) > 0:
        # save record
        file_name_json = f'{now.strftime("%Y-%m-%d-%H")}.json'
        file_path = os.path.join(dir_prefix, folder_name, file_name_json)
        with open(file_path, 'w') as fout:
            json.dump(all_files, fout)
        # store file
        with open(path, 'w') as fout:
            for cid in fresh_file_cids:
                fout.write(cid + '\n')
        # update all daily fresh file cid
        with open(all_daily_fresh_file, 'a') as fout:
            for cid in fresh_file_cids:
                fout.write(cid + '\n')
    else:
        exit(0)


if __name__ == '__main__':
    # start parser
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-n', '--new', type=int, help="if specified new collecting, value represents collecting period "
    #                                                   "(days)")
    # args = parser.parse_args()
    # if args.new:
    #     duration = args.new
    #     if duration < 1:
    #         print("Error, duration cannot be less than 1 days")
    #         exit(1)
    # else:
    #     duration = 0
    prefix = './data'
    main(prefix)
