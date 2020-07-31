import csv


def sort_params(params_str):
    params = params_str.split(',')
    return ','.join(sorted(params))


def get_dataset():
    filename = "data/export-oneh.csv"
    dataset = {}
    with open(filename, encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            uid, command, params, os_type, source, begin, end = row
            params = sort_params(params)
            if reader.line_num == 1:
                continue
            if uid not in dataset:
                dataset[uid] = [(command, params, os_type, source, begin, end)]
            else:
                last_cmd, last_params, *_ = dataset[uid][-1]
                last_params = sort_params(last_params)
                if last_cmd == command and last_params == params:
                    continue  # duplicate
                dataset[uid].append(
                    (command, params, os_type, source, begin, end))
    return dataset


if __name__ == "__main__":
    get_dataset()
