import argparse
import signal
from conf import *
from libc import *
from feedback import *
from execution import *
from seed import *
from schedule import *
from mutation import *


FORKSRV_FD = 198


# listen for user's signal
def signal_handler(sig, frame):
    print('You pressed Ctrl+C! Ending the fuzzing session...')
    sys.exit(0)


def run_forkserver(conf, ctl_read_fd, st_write_fd):
    os.dup2(ctl_read_fd, FORKSRV_FD)
    os.dup2(st_write_fd, FORKSRV_FD + 1)
    # prepare command
    cmd = [conf['target']] + conf['target_args']
    print(cmd)
    print(f'shmid is {os.environ[SHM_ENV_VAR]}')
    print(f'st_write_fd: {st_write_fd}')

    # eats stdout and stderr of the target
    dev_null_fd = os.open(os.devnull, os.O_RDWR)
    os.dup2(dev_null_fd, 1)
    os.dup2(dev_null_fd, 2)

    os.execv(conf['target'], cmd)


def run_fuzzing(conf, st_read_fd, ctl_write_fd, trace_bits):

    read_bytes = os.read(st_read_fd, 4)
    if len(read_bytes) == 4:
        print("forkserver is up! starting fuzzing... press Ctrl+C to stop")

    seed_queue = []
    global_bitmap = {}
    # do the dry run, check if the target is working and initialize the seed queue
    shutil.copytree(conf['seeds_folder'], conf['queue_folder'])
    for i, seed_file in enumerate(os.listdir(conf['queue_folder'])):
        seed_path = os.path.join(conf['queue_folder'], seed_file)
        # copy the seed content to "current_input"
        shutil.copyfile(seed_path, conf['current_input'])
        # run the target with the seed
        status_code, exec_time = run_target(ctl_write_fd, st_read_fd, trace_bits)

        if status_code == 9:
            print(f"Seed {seed_file} caused a timeout during the dry run")
            sys.exit(0)

        if check_crash(status_code):
            print(f"Seed {seed_file} caused a crash during the dry run")
            sys.exit(0)

        new_edge_covered, coverage = check_coverage(trace_bits, global_bitmap)
        file_size = os.path.getsize(conf['current_input'])

        new_seed = Seed(seed_path, i, coverage, exec_time, file_size)

        seed_queue.append(new_seed)

    print("Dry run finished. Now starting the fuzzing loop...")
    # start the fuzzing loop
    while True:
        selected_seed = select_next_seed(seed_queue, len(global_bitmap))

        stats = calculate_statistics(seed_queue)
        power_schedule = get_power_schedule(selected_seed, *stats)
        # print(global_bitmap)
        # print(f"Power schedule: {power_schedule}")

        # generate new test inputs according to the power schedule for the selected seed
        for i in range(0, power_schedule):
            # TODO: implement the strategy for selecting a mutation operator
            havoc_mutation(conf, selected_seed, seed_queue)
            # run the target with the mutated seed
            status_code, exec_time = run_target(ctl_write_fd, st_read_fd, trace_bits)

            if status_code == 9:
                print("Timeout, skipping this input")
                continue

            if check_crash(status_code):
                print(f"Found a crash, status code is {status_code}")
                filename = str(len(os.listdir(conf['crashes_folder'])))
                crash_path = os.path.join(conf['crashes_folder'], filename)

                # Make the file name and path
                shutil.copyfile(conf['current_input'], crash_path)

                continue

            new_edge_covered, coverage = check_coverage(trace_bits, global_bitmap)

            # coverage is the total hits
            if new_edge_covered:
                # print("Found new coverage!")
                filename = str(len(os.listdir(conf['queue_folder'])))
                queue_path = os.path.join(conf['queue_folder'], filename)

                # Make the file name and path
                shutil.copyfile(conf['current_input'], queue_path)
                file_size = os.path.getsize(conf['current_input'])

                new_seed = Seed(queue_path, filename, coverage, exec_time, file_size)
                seed_queue.append(new_seed)

                continue


def main():

    print("====== Welcome to use Mini-Lop ======")

    parser = argparse.ArgumentParser(description='Mini-Lop: A lightweight grey-box fuzzer')

    parser.add_argument('--config', '-c', required=True, help='Path to config file', type=str)

    args = parser.parse_args()

    config_path = os.path.abspath(args.config)

    config_valid, conf = parse_config(config_path)

    if not config_valid:
        print("Config file is not valid")
        return

    libc = get_libc()

    shmid, trace_bits = setup_shm(libc)
    # share the shmid with the target via an environment variable
    os.environ[SHM_ENV_VAR] = str(shmid)
    # clean the shared memory
    clear_shm(trace_bits)

    signal.signal(signal.SIGINT, signal_handler)

    # setup pipes for communication
    # st: status, ctl: control
    (st_read_fd, st_write_fd) = os.pipe()
    (ctl_read_fd, ctl_write_fd) = os.pipe()

    child_pid = os.fork()

    if child_pid == 0:
        run_forkserver(conf, ctl_read_fd, st_write_fd)
    else:
        run_fuzzing(conf, st_read_fd, ctl_write_fd, trace_bits)


if __name__ == '__main__':
    main()
