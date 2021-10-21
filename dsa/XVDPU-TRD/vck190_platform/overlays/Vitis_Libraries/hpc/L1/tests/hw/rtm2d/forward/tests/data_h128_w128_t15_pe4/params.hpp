/*
 * Copyright 2019 Xilinx, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
*/
#pragma once
#define ORDER 8
#define WIDTH 128
#define HEIGHT 128
#define NTime 15
#define NXB 20
#define NZB 20
#define NX (WIDTH - 2 * NXB)
#define NZ (HEIGHT - 2 * NZB)
#define NUM_INST 3
#define nPE 4
typedef float DATATYPE;
