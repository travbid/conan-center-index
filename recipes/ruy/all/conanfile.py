import os
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import get, replace_in_file, rm
from conan.tools.scm import Version

required_conan_version = ">=1.55.0"


class RuyConan(ConanFile):
    name = "ruy"
    description = "ruy is a matrix multiplication library.\n" \
                  "Its focus is to cover the matrix multiplication needs of neural network inference engines\n"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/google/ruy"
    license = "Apache-2.0"
    topics = ("matrix", "multiplication", "neural", "network", "AI", "tensorflow")
    exports_sources = "CMakeLists.txt"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    @property
    def _minimum_compilers_version(self):
        return {
            "Visual Studio": "15",
            "gcc": "5",
            "clang": "3.4",
            "apple-clang": "5.1",
        }

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, 14)

        minimum_version = self._minimum_compilers_version.get(str(self.settings.compiler), False)
        if not minimum_version:
            self.output.warn("Compiler is unknown. Assuming it supports C++14.")
        elif Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration("Build requires support for C++14. Minimum version for {} is {}"
                                            .format(str(self.settings.compiler), minimum_version))

        if str(self.settings.compiler) == "clang" and Version(self.settings.compiler.version) <= "5" and self.settings.build_type == "Debug":
            raise ConanInvalidConfiguration(
                "Debug builds are not supported on older versions of Clang (<=5)")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("cpuinfo/cci.20201217")

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
            destination=self.source_folder, strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["RUY_MINIMAL_BUILD"] = True
        tc.variables["RUY_ENABLE_INSTALL"] = True
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        # 1. Allow Shared builds
        replace_in_file(self, os.path.join(self.source_folder, "cmake", "ruy_cc_library.cmake"),
                        "add_library(${_NAME} STATIC",
                        "add_library(${_NAME}"
                        )
        replace_in_file(self, os.path.join(self.source_folder, "cmake", "ruy_cc_library.cmake"),
                        "file(RELATIVE_PATH _SUBDIR ${CMAKE_SOURCE_DIR} ${CMAKE_CURRENT_LIST_DIR})",
                        "file(RELATIVE_PATH _SUBDIR ${CMAKE_SOURCE_DIR}/" +
                        self.source_folder + " ${CMAKE_CURRENT_LIST_DIR})"
                        )

        # 2. Shared builds fail with undefined symbols without this fix.
        # This is because ruy only links to 'cpuinfo' but it also needs 'clog' (from the same package)
        cpuinfoLibs = self.deps_cpp_info["cpuinfo"].libs + self.deps_cpp_info["cpuinfo"].system_libs
        libsListAsString = ";".join(cpuinfoLibs)
        if int(self.version.strip('cci.')) < 20220628:
            replace_in_file(self, os.path.join(self.source_folder, "ruy", "CMakeLists.txt"),
                            "set(ruy_6_cpuinfo \"cpuinfo\")",
                            f"set(ruy_6_cpuinfo \"{libsListAsString}\")"
                            )
        else:
            replace_in_file(self, os.path.join(self.source_folder, "ruy", "CMakeLists.txt"),
                            "set(ruy_6_cpuinfo_cpuinfo \"cpuinfo::cpuinfo\")",
                            f"set(ruy_6_cpuinfo_cpuinfo \"{libsListAsString}\")"
                            )
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, os.pardir))
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        self.copy("LICENSE", dst="licenses", src=self.source_folder)
        rm(self, "*.pdb", self.package_folder)

    def package_info(self):
        self.cpp_info.libs = ["ruy_frontend",
                            "ruy_context",
                            "ruy_trmul",
                            "ruy_thread_pool",
                            "ruy_blocking_counter",
                            "ruy_prepare_packed_matrices",
                            "ruy_ctx",
                            "ruy_allocator",
                            "ruy_prepacked_cache",
                            "ruy_tune",
                            "ruy_wait",
                            "ruy_apply_multiplier",
                            "ruy_block_map",
                            "ruy_context_get_ctx",
                            "ruy_cpuinfo",
                            "ruy_denormal",
                            "ruy_have_built_path_for_avx",
                            "ruy_have_built_path_for_avx2_fma",
                            "ruy_have_built_path_for_avx512",
                            "ruy_kernel_arm",
                            "ruy_kernel_avx",
                            "ruy_kernel_avx2_fma",
                            "ruy_kernel_avx512",
                            "ruy_pack_arm",
                            "ruy_pack_avx",
                            "ruy_pack_avx2_fma",
                            "ruy_pack_avx512",
                            "ruy_system_aligned_alloc",
                            "ruy_profiler_instrumentation",
                            "ruy_profiler_profiler"
                            ]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "pthread"])
