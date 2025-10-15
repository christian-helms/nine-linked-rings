CXX      := g++

#CXXFLAGS := -pedantic-errors -Wall -Wextra -Werror -g --std=c++17 -fPIC
CXXFLAGS := -g --std=c++17 -fPIC
LDFLAGS  := -L./ManusSDK/lib -lManusSDK -lncurses -Wl,-rpath=/usr/lib/manus
BUILD    := ./
OBJ_DIR  := $(BUILD)/objects
APP_DIR  := $(BUILD)
LIB_NAME := libmanus-vive-isaaclab-bridge.so
TARGET   := $(LIB_NAME)
INCLUDE  := -I./ManusSDK/include
SRC      :=  \
   $(wildcard *.cpp)

OBJECTS  := $(SRC:%.cpp=$(OBJ_DIR)/%.o)
DEPENDENCIES \
         := $(OBJECTS:.o=.d)

all: build $(APP_DIR)/$(TARGET)

$(OBJ_DIR)/%.o: %.cpp
	@mkdir -p $(@D)
	$(CXX) $(CXXFLAGS) $(INCLUDE) -c $< -MMD -o $@

$(APP_DIR)/$(TARGET): $(OBJECTS)
	@mkdir -p $(@D)
	$(CXX) $(CXXFLAGS) -shared -o $(APP_DIR)/$(TARGET) $^ $(LDFLAGS)
	
-include $(DEPENDENCIES)

.PHONY: all build clean debug release info install uninstall

build:
	@mkdir -p $(APP_DIR)
	@mkdir -p $(OBJ_DIR)

debug: CXXFLAGS += -DDEBUG -g
debug: all

release: CXXFLAGS += -g
release: all

clean:
	-@rm -f $(APP_DIR)/$(TARGET)
	-@rm -rvf $(OBJ_DIR)/*

info:
	@echo "[*] Library name:    ${LIB_NAME}    "
	@echo "[*] Application dir: ${APP_DIR}     "
	@echo "[*] Object dir:      ${OBJ_DIR}     "
	@echo "[*] Sources:         ${SRC}         "
	@echo "[*] Objects:         ${OBJECTS}     "
	@echo "[*] Dependencies:    ${DEPENDENCIES}"
