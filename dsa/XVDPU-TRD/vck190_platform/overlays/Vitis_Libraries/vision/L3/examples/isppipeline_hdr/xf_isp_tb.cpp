/*
 * Copyright 2021 Xilinx, Inc.
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

#include "common/xf_headers.hpp"
#include "xf_isp_types.h"

#include "xcl2.hpp"

int g_value_com(unsigned short& value_in, float& alpha, float& ob) {
    float radiance_out = (value_in - ob) / alpha;

    return radiance_out;
}

double compute_datareliabilityweight(float& C, float& mu_h, float& mu_l, float& r) {
    double wr;

    if (r < mu_l)
        wr = exp(-C * (std::pow((r - mu_l), 2)));
    else if (r < mu_h)
        wr = 1;
    else
        wr = exp(-C * (std::pow((r - mu_h), 2)));

    return wr;
}

void compute_gamma(float r_g, float g_g, float b_g, uchar gamma_lut[256 * 3]) {
    float gamma_inv[256] = {
        0.000000, 0.003922, 0.007843, 0.011765, 0.015686, 0.019608, 0.023529, 0.027451, 0.031373, 0.035294, 0.039216,
        0.043137, 0.047059, 0.050980, 0.054902, 0.058824, 0.062745, 0.066667, 0.070588, 0.074510, 0.078431, 0.082353,
        0.086275, 0.090196, 0.094118, 0.098039, 0.101961, 0.105882, 0.109804, 0.113725, 0.117647, 0.121569, 0.125490,
        0.129412, 0.133333, 0.137255, 0.141176, 0.145098, 0.149020, 0.152941, 0.156863, 0.160784, 0.164706, 0.168627,
        0.172549, 0.176471, 0.180392, 0.184314, 0.188235, 0.192157, 0.196078, 0.200000, 0.203922, 0.207843, 0.211765,
        0.215686, 0.219608, 0.223529, 0.227451, 0.231373, 0.235294, 0.239216, 0.243137, 0.247059, 0.250980, 0.254902,
        0.258824, 0.262745, 0.266667, 0.270588, 0.274510, 0.278431, 0.282353, 0.286275, 0.290196, 0.294118, 0.298039,
        0.301961, 0.305882, 0.309804, 0.313725, 0.317647, 0.321569, 0.325490, 0.329412, 0.333333, 0.337255, 0.341176,
        0.345098, 0.349020, 0.352941, 0.356863, 0.360784, 0.364706, 0.368627, 0.372549, 0.376471, 0.380392, 0.384314,
        0.388235, 0.392157, 0.396078, 0.400000, 0.403922, 0.407843, 0.411765, 0.415686, 0.419608, 0.423529, 0.427451,
        0.431373, 0.435294, 0.439216, 0.443137, 0.447059, 0.450980, 0.454902, 0.458824, 0.462745, 0.466667, 0.470588,
        0.474510, 0.478431, 0.482353, 0.486275, 0.490196, 0.494118, 0.498039, 0.501961, 0.505882, 0.509804, 0.513725,
        0.517647, 0.521569, 0.525490, 0.529412, 0.533333, 0.537255, 0.541176, 0.545098, 0.549020, 0.552941, 0.556863,
        0.560784, 0.564706, 0.568627, 0.572549, 0.576471, 0.580392, 0.584314, 0.588235, 0.592157, 0.596078, 0.600000,
        0.603922, 0.607843, 0.611765, 0.615686, 0.619608, 0.623529, 0.627451, 0.631373, 0.635294, 0.639216, 0.643137,
        0.647059, 0.650980, 0.654902, 0.658824, 0.662745, 0.666667, 0.670588, 0.674510, 0.678431, 0.682353, 0.686275,
        0.690196, 0.694118, 0.698039, 0.701961, 0.705882, 0.709804, 0.713725, 0.717647, 0.721569, 0.725490, 0.729412,
        0.733333, 0.737255, 0.741176, 0.745098, 0.749020, 0.752941, 0.756863, 0.760784, 0.764706, 0.768627, 0.772549,
        0.776471, 0.780392, 0.784314, 0.788235, 0.792157, 0.796078, 0.800000, 0.803922, 0.807843, 0.811765, 0.815686,
        0.819608, 0.823529, 0.827451, 0.831373, 0.835294, 0.839216, 0.843137, 0.847059, 0.850980, 0.854902, 0.858824,
        0.862745, 0.866667, 0.870588, 0.874510, 0.878431, 0.882353, 0.886275, 0.890196, 0.894118, 0.898039, 0.901961,
        0.905882, 0.909804, 0.913725, 0.917647, 0.921569, 0.925490, 0.929412, 0.933333, 0.937255, 0.941176, 0.945098,
        0.949020, 0.952941, 0.956863, 0.960784, 0.964706, 0.968627, 0.972549, 0.976471, 0.980392, 0.984314, 0.988235,
        0.992157, 0.996078, 1.000000};

    unsigned char gam_r = 0, gam_g = 0, gam_b = 0;

    for (int i = 0; i < 256; ++i) {
        float r_inv = (float)1 / r_g;
        float g_inv = (float)1 / g_g;
        float b_inv = (float)1 / b_g;
        float powval_r = (float)std::pow(gamma_inv[i], r_inv);
        short tempgamma_r = (powval_r * 255.0);

        if (tempgamma_r > 255) {
            gam_r = 255;
        } else {
            gam_r = tempgamma_r;
        }

        float powval_g = (float)std::pow(gamma_inv[i], g_inv);
        short tempgamma_g = (powval_g * 255.0);

        if (tempgamma_g > 255) {
            gam_g = 255;
        } else {
            gam_g = tempgamma_g;
        }

        float powval_b = (float)std::pow(gamma_inv[i], b_inv);
        short tempgamma_b = (powval_b * 255.0);

        if (tempgamma_b > 255) {
            gam_b = 255;
        } else {
            gam_b = tempgamma_b;
        }
        gamma_lut[i] = gam_r;
        gamma_lut[i + 256] = gam_g;
        gamma_lut[i + 512] = gam_b;
    }
}

void HDR_merge(cv::Mat& _src1,
               cv::Mat& _src2,
               float& alpha,
               float& optical_black_value,
               float& intersec,
               float& rho,
               float& imax,
               float* t,
               cv::Mat& final_img,
               short wr_ocv[NO_EXPS][W_B_SIZE]) {
    int m = NO_EXPS;

    float gamma_out[NO_EXPS] = {0.0, 0.0};
    for (int i = 0; i < m - 1; i++) {
        gamma_out[i] = (rho * (imax - optical_black_value) - optical_black_value * (imax - rho)) /
                       (t[i] * rho + t[i + 1] * (imax - rho));
    }

    float mu_h[NO_EXPS] = {0.0, 0.0};
    float mu_l[NO_EXPS] = {0.0, 0.0};

    for (int i = 0; i < m - 1; i++) {
        if (i == 0) {
            float value = (rho - optical_black_value) / alpha;
            mu_h[i] = value / t[0];
        } else {
            mu_h[i] = gamma_out[i] - (gamma_out[i - 1] - mu_h[i - 1]);
        }

        mu_l[i + 1] = 2 * gamma_out[i] - mu_h[i];
    }

    float value_max = (imax - optical_black_value) / alpha;
    mu_h[m - 1] = value_max / t[m - 1];

    float c_inters = -(log(intersec) / (std::pow((gamma_out[0] - mu_h[0]), 2)));

    double wr[NO_EXPS][W_B_SIZE];

    FILE* fp = fopen("weights.txt", "w");
    for (int i = 0; i < NO_EXPS; i++) {
        for (int j = 0; j < (W_B_SIZE); j++) {
            float rv = (float)(j / t[i]);
            wr[i][j] = compute_datareliabilityweight(c_inters, mu_h[i], mu_l[i], rv);
            wr_ocv[i][j] = wr[i][j] * 16384;
            fprintf(fp, "%lf,", wr[i][j]);
        }
        fprintf(fp, "\n");
    }
    fclose(fp);

    cv::Mat final_w1, final_w2;

    final_img.create(_src1.rows, _src1.cols, CV_16UC1);
    final_w1.create(_src1.rows, _src1.cols, CV_32FC1);
    final_w2.create(_src1.rows, _src1.cols, CV_32FC1);

    FILE* fp1 = fopen("imagevals_ocv.txt", "w");

    for (int i = 0; i < _src1.rows; i++) {
        for (int j = 0; j < _src1.cols; j++) {
            int val1 = _src1.at<unsigned short>(i, j);
            int val2 = _src2.at<unsigned short>(i, j);

            final_w1.at<float>(i, j) = (float)(wr[0][val1]);
            final_w2.at<float>(i, j) = (float)(wr[1][val2]);

            float val_1 = final_w1.at<float>(i, j) *
                          val1; // (g_value_com(_src1.at<unsigned short>(i,j),alpha,optical_black_value)/t[0]);
            float val_2 = final_w2.at<float>(i, j) *
                          val2; //(g_value_com(_src2.at<unsigned short>(i,j),alpha,optical_black_value)/t[1]);

            float sum_wei = final_w1.at<float>(i, j) + final_w2.at<float>(i, j);

            int final_val = (int)((float)(val_1 + val_2) / (float)sum_wei);

            if (final_val > (W_B_SIZE - 1)) {
                final_val = (W_B_SIZE - 1);
            }
            fprintf(fp1, "%d,", final_val);

            final_img.at<unsigned short>(i, j) = (unsigned short)final_val;
        }
        fprintf(fp1, "\n");
    }
    fclose(fp1);
}

int main(int argc, char** argv) {
    if (argc != 3) {
        fprintf(stderr, "Invalid Number of Arguments!\nUsage:\n");
        fprintf(stderr, "<Executable Name> <input image path> \n");
        return -1;
    }

    cv::Mat in_img1, in_img2, final_ocv, out_img, ocv_ref, in_gray, diff;

    unsigned short in_width, in_height;

/*  reading in the color image  */
#if T_8U
    in_img1 = cv::imread(argv[1], 0); // read image
    in_img2 = cv::imread(argv[2], 0); // read image

#else
    in_img1 = cv::imread(argv[1], -1); // read image
    in_img2 = cv::imread(argv[2], -1); // read image
#endif

    if (in_img1.data == NULL) {
        fprintf(stderr, "Cannot open image at %s\n", argv[1]);
        return 0;
    }

#if T_8U
    out_img.create(in_img1.rows, in_img1.cols, CV_8UC3);
    size_t vec_in_size_bytes = 256 * 3 * sizeof(unsigned char);
    size_t vec_weight_size_bytes = NO_EXPS * XF_NPPC * W_B_SIZE * sizeof(short);
    size_t image_in_size_bytes = in_img1.rows * in_img1.cols * sizeof(unsigned char);
    size_t image_out_size_bytes = in_img1.rows * in_img1.cols * 3 * sizeof(unsigned char);
#else
    out_img.create(in_img1.rows, in_img1.cols, CV_8UC3);
    size_t vec_in_size_bytes = 256 * 3 * sizeof(unsigned char);
    size_t vec_weight_size_bytes = NO_EXPS * XF_NPPC * W_B_SIZE * sizeof(short);
    size_t image_in_size_bytes = in_img1.rows * in_img1.cols * sizeof(unsigned short);
    size_t image_out_size_bytes = in_img1.rows * in_img1.cols * 3 * sizeof(unsigned char);
#endif

    // Write input image
    imwrite("input1.png", in_img1);
    imwrite("input2.png", in_img2);

#if T_8U
    final_ocv.create(in_img1.rows, in_img1.cols, CV_8UC1);
#endif
#if T_16U
    final_ocv.create(in_img1.rows, in_img1.cols, CV_16UC1);
#endif

    float alpha = 1.0f;
    float optical_black_value = 0.0f;
    float intersec = 0.25f;
    float rho = 512;
    float imax = (W_B_SIZE - 1);
    float t[NO_EXPS] = {1.0f, 0.25f}; //{1.0f,0.25f,0.0625f};

    short wr_ocv[NO_EXPS][W_B_SIZE];

    HDR_merge(in_img1, in_img2, alpha, optical_black_value, intersec, rho, imax, t, final_ocv, wr_ocv);

    short wr_hls[NO_EXPS * XF_NPPC * W_B_SIZE];

    for (int k = 0; k < XF_NPPC; k++) {
        for (int i = 0; i < NO_EXPS; i++) {
            for (int j = 0; j < (W_B_SIZE); j++) {
                wr_hls[(i + k * XF_NPPC) * W_B_SIZE + j] = wr_ocv[i][j];
            }
        }
    }

    /////////////////////////////////////// CL ////////////////////////

    int height = in_img1.rows;
    int width = in_img1.cols;

    unsigned short rgain = 153;
    unsigned short bgain = 140;

    unsigned char mode_reg = 1;

    unsigned short pawb = 256;

    unsigned char gamma_lut[256 * 3];
    uint32_t hist0_awb[3][HIST_SIZE] = {0};
    uint32_t hist1_awb[3][HIST_SIZE] = {0};

    float gamma_val_r = 1.5f, gamma_val_g = 1.5f, gamma_val_b = 1.5f;

    compute_gamma(gamma_val_r, gamma_val_g, gamma_val_b, gamma_lut);

    // int channels=out_img.channels();

    cl_int err;
    std::cout << "INFO: Running OpenCL section." << std::endl;

    std::vector<cl::Device> devices = xcl::get_xil_devices();
    cl::Device device = devices[0];
    OCL_CHECK(err, cl::Context context(device, NULL, NULL, NULL, &err));
    OCL_CHECK(err, cl::CommandQueue q(context, device, CL_QUEUE_PROFILING_ENABLE, &err));

    std::string device_name = device.getInfo<CL_DEVICE_NAME>();
    std::string binaryFile = xcl::find_binary_file(device_name, "krnl_ISPPipeline");
    cl::Program::Binaries bins = xcl::import_binary_file(binaryFile);
    devices.resize(1);

    OCL_CHECK(err, cl::Program program(context, devices, bins, NULL, &err));

    // Create a kernel:
    OCL_CHECK(err, cl::Kernel kernel(program, "ISPPipeline_accel", &err));

    std::vector<cl::Memory> inBufVec1, inBufVec2, outBufVec;
    OCL_CHECK(err, cl::Buffer imageToDevice1(context, CL_MEM_READ_ONLY, image_in_size_bytes, NULL, &err));
    OCL_CHECK(err, cl::Buffer imageToDevice2(context, CL_MEM_READ_ONLY, image_in_size_bytes, NULL, &err));
    OCL_CHECK(err, cl::Buffer imageFromDevice(context, CL_MEM_WRITE_ONLY, image_out_size_bytes, NULL, &err));
    OCL_CHECK(err, cl::Buffer buffer_inVec(context, CL_MEM_READ_ONLY, vec_in_size_bytes, NULL, &err));
    OCL_CHECK(err, cl::Buffer buffer_inVec_Weights(context, CL_MEM_READ_ONLY, vec_weight_size_bytes, NULL, &err));

    // Set the kernel arguments
    OCL_CHECK(err, err = kernel.setArg(0, imageToDevice1));
    OCL_CHECK(err, err = kernel.setArg(1, imageToDevice2));
    OCL_CHECK(err, err = kernel.setArg(2, imageFromDevice));
    OCL_CHECK(err, err = kernel.setArg(3, height));
    OCL_CHECK(err, err = kernel.setArg(4, width));
    OCL_CHECK(err, err = kernel.setArg(5, rgain));
    OCL_CHECK(err, err = kernel.setArg(6, bgain));
    OCL_CHECK(err, err = kernel.setArg(7, buffer_inVec));
    OCL_CHECK(err, err = kernel.setArg(8, mode_reg));
    OCL_CHECK(err, err = kernel.setArg(9, pawb));
    OCL_CHECK(err, err = kernel.setArg(10, buffer_inVec_Weights));

    for (int i = 0; i < 2; i++) {
        OCL_CHECK(err, q.enqueueWriteBuffer(buffer_inVec,      // buffer on the FPGA
                                            CL_TRUE,           // blocking call
                                            0,                 // buffer offset in bytes
                                            vec_in_size_bytes, // Size in bytes
                                            gamma_lut));

        OCL_CHECK(err, q.enqueueWriteBuffer(buffer_inVec_Weights,  // buffer on the FPGA
                                            CL_TRUE,               // blocking call
                                            0,                     // buffer offset in bytes
                                            vec_weight_size_bytes, // Size in bytes
                                            wr_hls));

        OCL_CHECK(err, q.enqueueWriteBuffer(imageToDevice1, CL_TRUE, 0, image_in_size_bytes, in_img1.data));
        OCL_CHECK(err, q.enqueueWriteBuffer(imageToDevice2, CL_TRUE, 0, image_in_size_bytes, in_img2.data));

        // Profiling Objects
        cl_ulong start = 0;
        cl_ulong end = 0;
        double diff_prof = 0.0f;
        cl::Event event_sp;

        // Launch the kernel
        OCL_CHECK(err, err = q.enqueueTask(kernel, NULL, &event_sp));
        clWaitForEvents(1, (const cl_event*)&event_sp);

        event_sp.getProfilingInfo(CL_PROFILING_COMMAND_START, &start);
        event_sp.getProfilingInfo(CL_PROFILING_COMMAND_END, &end);
        diff_prof = end - start;
        std::cout << (diff_prof / 1000000) << "ms" << std::endl;

        // Copying Device result data to Host memory
        q.enqueueReadBuffer(imageFromDevice, CL_TRUE, 0, image_out_size_bytes, out_img.data);
    }

    q.finish();

    /////////////////////////////////////// end of CL ////////////////////////

    // Write output image
    imwrite("hls_out.png", out_img);

    return 0;
}
