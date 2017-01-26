#include <stdlib.h>
#include <stdio.h>
#include <error.h>
#include <string.h>
#include <asm/types.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/socket.h>
#include <linux/netlink.h>

int main(void) {
    struct sockaddr_nl sa;

    memset(&sa, 0, sizeof(sa));
    sa.nl_family = AF_NETLINK;
    sa.nl_pid = getpid();
    sa.nl_groups = NETLINK_KOBJECT_UEVENT;

    int sock = socket(AF_NETLINK, SOCK_RAW, 
                                  NETLINK_KOBJECT_UEVENT);
    if (sock < 0) { perror("failed to create sock!\n"); }
    bind(sock, (struct sockaddr *) &sa, sizeof(sa));

    char buf[4096];

    struct iovec iv = {
        .iov_base = buf,
        .iov_len = sizeof(buf),
    };

    struct sockaddr_nl msg_sa;

    struct msghdr msg = {
        .msg_name = &msg_sa,
        .msg_namelen = sizeof(msg_sa),
        .msg_iov = &iv,
        .msg_iovlen = 1,
        .msg_control = NULL,
        .msg_controllen = 0,
        .msg_flags = 0,
    };

    ssize_t len = recvmsg(sock, &msg, 0);
    for (; len > 0; len = recvmsg(sock, &msg, 0)) {
        if (strncmp("libudev", buf, strlen("libudev")) == 0) {
            continue;
        }

        for (int i = 0; i < len; i++) {
            if (buf[i] == 0x0) {
                printf("\n");
            } else {
                printf("%c", buf[i]);
            }
        }
        printf("---EOM---\n");
    }

    return 0;
}

