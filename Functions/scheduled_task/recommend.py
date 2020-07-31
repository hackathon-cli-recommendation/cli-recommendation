import mock_data
from command_table import CommandTable


def print_cmd(nx_cmd):
    cmd, params, confidence = nx_cmd
    print("{:.2f}% people use run this command: {} {}".format(confidence*100, cmd, ' '.join(params.split(','))))


def test_cmd(cmd_table, cmd, params):
    print("After run {} {}".format(cmd, params))
    print_cmd(cmd_table.get_next_command(cmd, params))


def main():
    dataset = mock_data.get_dataset()
    cmd_table = CommandTable()
    cmd_table.update_table(dataset)
    dist, cnt, cmd_cnt = cmd_table.analyze_params()
    print("Dist: {}, cnt: {}, cmd_cnt: {}, perc: {}".format(dist, cnt, cmd_cnt, dist/cnt))

    # nx_cmd = cmd_table.get_next_command(
    #     "account get-access-token", "-o,--resource")
    # nx_cmd = cmd_table.get_next_command("vm create", "")
    # print_cmd(nx_cmd)
    # test_cmd(cmd_table, "vm list", "")
    # test_cmd(cmd_table, "webapp create", "")
    # test_cmd(cmd_table, "login", "--identity")
    # test_cmd(cmd_table, "keyvault secret show", "")
    # test_cmd(cmd_table, "group deployment create", "")
    # test_cmd(cmd_table, "backup policy list", "")


if __name__ == "__main__":
    main()
