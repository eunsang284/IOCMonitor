# EPICS Alive Server Build Makefile for Build Directory
# EPICS Alive 서버 빌드 디렉토리용 Makefile
# Compiles EPICS Alive Server source files in a separate build directory
# 별도의 빌드 디렉토리에서 EPICS Alive 서버 소스 파일을 컴파일합니다

# Build directory (passed from parent Makefile) / 빌드 디렉토리 (상위 Makefile에서 전달)
ifndef BUILD_DIR
  BUILD_DIR = .
endif

# Source directory (relative to this makefile) / 소스 디렉토리 (이 makefile 기준 상대 경로)
SRC_DIR = ../../alive-server/src

# Compiler settings / 컴파일러 설정
CC = gcc -Wall
AR = ar
CFLAGS = -O2

# for debugging / 디버깅용
# CFLAGS += -g

# Safety default for configuration file / 설정 파일의 안전 기본값
ifndef Cfg_File
  Cfg_File = ../../config/alived_config.txt
endif

# Export configuration file path / 설정 파일 경로 내보내기
export Cfg_File

# Object files (in build directory) / 오브젝트 파일들 (빌드 디렉토리 내)
OBJS = alived.o llrb_db.o iocdb.o iocdb_access.o utility.o logging.o gentypes.o notifydb.o config_parse.o
ALIVECTL_OBJS = alivectl.o config_parse.o
EVENT_DUMP_OBJS = event_dump.o config_parse.o

.PHONY: all clean

# Main target / 메인 타겟
all: alived alivectl event_dump

# alived executable / alived 실행 파일
alived: $(OBJS)
	@echo "Linking alived..."
	$(CC) -pthread $(OBJS) -o $(BUILD_DIR)/alived

# alivectl executable / alivectl 실행 파일
alivectl: $(ALIVECTL_OBJS)
	@echo "Linking alivectl..."
	$(CC) $(ALIVECTL_OBJS) -o $(BUILD_DIR)/alivectl

# event_dump executable / event_dump 실행 파일
event_dump: $(EVENT_DUMP_OBJS)
	@echo "Linking event_dump..."
	$(CC) $(EVENT_DUMP_OBJS) -o $(BUILD_DIR)/event_dump

# Object file compilation rules / 오브젝트 파일 컴파일 규칙
alived.o: $(SRC_DIR)/alived.c $(SRC_DIR)/alived.h
	@echo "Compiling alived.c..."
	$(CC) $(CFLAGS) -c $(SRC_DIR)/alived.c -o alived.o

llrb_db.o: $(SRC_DIR)/llrb_db.c $(SRC_DIR)/llrb_db.h
	@echo "Compiling llrb_db.c..."
	$(CC) $(CFLAGS) -c $(SRC_DIR)/llrb_db.c -o llrb_db.o

iocdb.o: $(SRC_DIR)/iocdb.c $(SRC_DIR)/iocdb.h $(SRC_DIR)/alived.h
	@echo "Compiling iocdb.c..."
	$(CC) $(CFLAGS) -c $(SRC_DIR)/iocdb.c -o iocdb.o

iocdb_access.o: $(SRC_DIR)/iocdb_access.c $(SRC_DIR)/iocdb_access.h $(SRC_DIR)/iocdb.h $(SRC_DIR)/alived.h
	@echo "Compiling iocdb_access.c..."
	$(CC) $(CFLAGS) -c $(SRC_DIR)/iocdb_access.c -o iocdb_access.o

utility.o: $(SRC_DIR)/utility.c $(SRC_DIR)/utility.h
	@echo "Compiling utility.c..."
	$(CC) $(CFLAGS) -c $(SRC_DIR)/utility.c -o utility.o

logging.o: $(SRC_DIR)/logging.c $(SRC_DIR)/logging.h $(SRC_DIR)/alived.h
	@echo "Compiling logging.c..."
	$(CC) $(CFLAGS) -c $(SRC_DIR)/logging.c -o logging.o

gentypes.o: $(SRC_DIR)/gentypes.c $(SRC_DIR)/gentypes.h
	@echo "Compiling gentypes.c..."
	$(CC) $(CFLAGS) -c $(SRC_DIR)/gentypes.c -o gentypes.o

notifydb.o: $(SRC_DIR)/notifydb.c $(SRC_DIR)/notifydb.h $(SRC_DIR)/alived.h
	@echo "Compiling notifydb.c..."
	$(CC) $(CFLAGS) -c $(SRC_DIR)/notifydb.c -o notifydb.o

config_parse.o: $(SRC_DIR)/config_parse.c $(SRC_DIR)/config_parse.h
	@echo "Compiling config_parse.c..."
	$(CC) $(CFLAGS) -DCFG_FILE=\"$(Cfg_File)\" -c $(SRC_DIR)/config_parse.c -o config_parse.o

alivectl.o: $(SRC_DIR)/alivectl.c
	@echo "Compiling alivectl.c..."
	$(CC) $(CFLAGS) -c $(SRC_DIR)/alivectl.c -o alivectl.o

event_dump.o: $(SRC_DIR)/event_dump.c
	@echo "Compiling event_dump.c..."
	$(CC) $(CFLAGS) -c $(SRC_DIR)/event_dump.c -o event_dump.o

# Clean build directory / 빌드 디렉토리 정리
clean:
	@echo "Cleaning build directory..."
	@rm -f *.o alived alivectl event_dump
	@echo "Build directory cleaned." 