#include <liburing.h>
#include <stdio.h>
int main(){
    struct io_uring ring;
    int ret = io_uring_queue_init(4, &ring, 0);
    if(ret==0){ printf("io_uring AVAILABLE\n"); io_uring_queue_exit(&ring); return 0; }
    printf("io_uring NOT AVAILABLE (err=%d)\n", ret); return 1;
}
