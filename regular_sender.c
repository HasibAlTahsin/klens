#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

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
    send(sock, msg, strlen(msg), 0);
    printf("regular send done\n");
    close(sock);
    return 0;
}
