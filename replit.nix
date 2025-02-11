{pkgs}: {
  deps = [
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
