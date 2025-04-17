CXX = g++

SRC = $(wildcard ./src/*.cpp) $(wildcard ../shared/*.cpp)
OBJ = $(SRC:.cpp=.o)
DEP = $(OBJ:.o=.d)

BINARY=xbatd
BIN_DESTINATION?=/usr/local/bin

SERVICE_PATH=./
SYS_DESTINATION?=/etc/systemd/system
SERVICE_NAME=xbatd.service

LIB_PATH?=/usr/local/share/xbatd/lib
LIB64_PATH?=/usr/local/share/xbatd/lib64
INCLUDE_PATH?=/usr/local/share/xbatd/include

LDFLAGS = -pthread -I$(INCLUDE_PATH) -L$(LIB_PATH) -L$(LIB64_PATH) -llikwid -lcurl -lquestdb_client -lstdc++fs -I /usr/local/cuda-*/targets/x86_64-linux/include/ -lnvidia-ml -lcrypto -I /opt/rocm-*/include -L /opt/rocm-*/lib -lamd_smi
BOOST = -lboost_log -lboost_log_setup -lboost_system -lboost_thread -DBOOST_LOG_DYN_LINK
CXXFLAGS = -std=c++17 -O2 -Wall -Wextra -Wpedantic $(LDFLAGS) $(BOOST)

$(BINARY): $(OBJ)
	$(CXX) -o $@ $^ $(CXXFLAGS)

-include $(DEP)

%.d: %.cpp 
	@$(CXX) $(CXXFLAGS) $< -MM -MT $(@:.d=.o) >$@

.PHONY: install
install:
	cp $(BINARY) $(BIN_DESTINATION)/$(BINARY)
	cp $(SERVICE_PATH)$(SERVICE_NAME) $(SYS_DESTINATION)/$(SERVICE_NAME)

.PHONY: uninstall
uninstall:
	rm -f $(BIN_DESTINATION)/$(BINARY)
	rm -f $(SYS_DESTINATION)/$(SERVICE_NAME)

.PHONY: clean
clean:
	rm -f $(OBJ) $(DEP) $(BINARY)