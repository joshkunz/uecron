#include <stdio.h>
#include <stdlib.h>
#include <linux/netlink.h>

int main(void) {
    return printf("%d", NETLINK_KOBJECT_UEVENT);
}
