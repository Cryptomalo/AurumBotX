{pkgs}: {
  deps = [
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.libxcrypt
    pkgs.rustc
    pkgs.libiconv
    pkgs.cargo
    pkgs.postgresql
    pkgs.openssl
    pkgs.opencl-headers
    pkgs.ocl-icd
    pkgs.glibcLocales
  ];
}
