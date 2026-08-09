#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <liburing.h>

int main(int argc, char **argv){
    int delay = argc>1 ? atoi(argv[1]) : 10;
    printf("PID=%d sending in %d sec\n", getpid(), delay);
    fflush(stdout);
    sleep(delay);

    int sock = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in addr = {.sin_family=AF_INET, .sin_port=htons(9999),
        .sin_addr.s_addr=inet_addr("127.0.0.1")};
    if(connect(sock,(struct sockaddr*)&addr,sizeof(addr))<0){perror("connect");return 1;}

    const char *msg = "{\"content\":\"Contact: sophie.dubois@orange.fr, +33 6 12 34 56 78\"}";

    struct io_uring ring;
    io_uring_queue_init(8, &ring, 0);
    struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
    io_uring_prep_send(sqe, sock, msg, strlen(msg), 0);
    io_uring_submit(&ring);
    struct io_uring_cqe *cqe;
    io_uring_wait_cqe(&ring, &cqe);
    printf("io_uring send done (res=%d)\n", cqe->res);
    io_uring_cqe_seen(&ring, cqe);
    io_uring_queue_exit(&ring);
    close(sock);
    return 0;
}
