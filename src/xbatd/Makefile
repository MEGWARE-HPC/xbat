CXX ?= g++

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

CUDA_INC := $(firstword $(wildcard /usr/local/cuda*/targets/x86_64-linux/include) \
                     $(wildcard /usr/local/cuda*/include) \
                     $(wildcard /usr/include))
ROCM_INC := $(firstword $(wildcard /opt/rocm*/include))
CPPFLAGS += -I$(INCLUDE_PATH) -I$(CUDA_INC) -I$(ROCM_INC)
CXXFLAGS += -std=c++17 -Wall -Wextra -Wpedantic -DBOOST_LOG_DYN_LINK
LIBDIRS := -L$(LIB_PATH) -L$(LIB64_PATH)
LINK_AUX := -Wl,-rpath-link,$(LIB_PATH) -Wl,-rpath-link,$(LIB64_PATH)
LDLIBS += -lboost_log -lboost_log_setup -lboost_system -lboost_thread \
            -llikwid -lcurl -lquestdb_client -lnvidia-ml -lamd_smi -lcrypto -lstdc++fs -pthread

$(BINARY): $(OBJ)
	$(CXX) -o $@ $^ $(LIBDIRS) $(LINK_AUX) $(LDFLAGS) $(LDLIBS)

-include $(DEP)

%.o: %.cpp
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c $< -o $@

%.d: %.cpp 
	@$(CXX) $(CPPFLAGS) $(CXXFLAGS) $< -MM -MT $(@:.d=.o) >$@

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