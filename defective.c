#include <stdio.h>
#include <stdlib.h>

int main() {
  int *ptr = (int*)malloc(10 * sizeof(int));
  ptr[10] = 5; // Buffer overflow
  free(ptr);
  return 0;
}
