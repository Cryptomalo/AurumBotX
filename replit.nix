{pkgs}: {
  deps = [
    pkgs.postgresql
    pkgs.openssl
    pkgs.opencl-headers
    pkgs.ocl-icd
    pkgs.glibcLocales
  ];
}
