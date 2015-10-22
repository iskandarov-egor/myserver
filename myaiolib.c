
#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <errno.h>
#include <stdlib.h>
#include <aio.h>

typedef struct {
	struct aiocb aiocb;
	 char *str;
} aiostruct;

void** askForFile(int fd, int offset, int BUF_SIZE, char *buf){
//printf( " askff \n");

  aiostruct **aiost = malloc(sizeof(aiostruct*));
  
  *aiost = malloc(sizeof(aiostruct));

  memset(&(*aiost)->aiocb, 0, sizeof(struct aiocb));
  //(*aiost)->str = malloc(BUF_SIZE + 1);
  
  //memset((*aiost)->str, 0, BUF_SIZE + 1);

  (*aiost)->aiocb.aio_offset = offset;
  (*aiost)->aiocb.aio_nbytes = BUF_SIZE;
  (*aiost)->aiocb.aio_fildes = fd;
  (*aiost)->aiocb.aio_buf = buf;

  if (aio_read(&((*aiost)->aiocb)) == -1) {
    printf("Error at aio_read() \n");
    exit(2);
  }
//printf( " askff end \n");  
  return aiost;
}

void cleanup(aiostruct** a) {
	free(*a);
}

int get0(){
	return 0;
}

int tryRead(aiostruct** a) {
  int err;
  if (((err = aio_error (&((**a).aiocb))) != EINPROGRESS) ){

	  //strcpy(dest, (**a).str);

	  err = aio_return(&((**a).aiocb));
	  cleanup(a);
		
	  return err;
	  
  } 
  
  return -22;
  
}


