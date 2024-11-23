import ctypes
import sys
import sysv_ipc

SHM_ENV_VAR   = "__AFL_SHM_ID"
MAP_SIZE_POW2 = 16
MAP_SIZE = (1 << MAP_SIZE_POW2)

def setup_shm(libc):
    # map functions
    shmget = libc.shmget
    shmat = libc.shmat

    shmat.restype = ctypes.c_void_p
    shmat.argtypes = (ctypes.c_int, ctypes.c_void_p, ctypes.c_int)

    # get the shared memory segment

    shmid = shmget(sysv_ipc.IPC_PRIVATE, MAP_SIZE, sysv_ipc.IPC_CREAT | sysv_ipc.IPC_EXCL | 0o600)

    if shmid < 0:
        sys.exit("cannot get shared memory segment with key %d" % (sysv_ipc.IPC_PRIVATE))

    # map the shared segment into the current process' memory
    # the location (size + 4096) is just a hint
    shmptr = shmat(shmid, None, 0)
    if shmptr == 0 or shmptr== -1:
        sys.exit("cannot attach shared memory segment with id %d" % (shmid))

    print(f'created shared memory, shmid: {shmid}')

    return shmid, shmptr


def clear_shm(trace_bits):
    ctypes.memset(trace_bits, 0, MAP_SIZE)


def check_crash(status_code):
    crashed = False
    if status_code == 6:
        crashed = True
        print("Found an abort!")
    elif status_code == 8:
        crashed = True
        print("Found a float-point error!")
    elif status_code == 11:
        crashed = True
        print("Found a segfault!")
    return crashed


def check_coverage(trace_bits, global_bitmap):
    raw_bitmap = ctypes.string_at(trace_bits, MAP_SIZE)
    total_hits = 0
    new_edge_covered = False

    # assumes that the xor was already instrumented in the fuzzing process
    # then it treats this bit map like an set of edges
    for id, byte in enumerate(raw_bitmap):
        # If means that it already hit
        if byte != 0:
            total_hits += 1
            if id not in global_bitmap:
                global_bitmap[id] = 0
                new_edge_covered = True
            else:
                global_bitmap[id] += 1
    print(f'covered {total_hits} edges')

    print(f'Total unique edges: {len(global_bitmap)}')

    return new_edge_covered, total_hits
