{pkgs}: {
  deps = [
    pkgs.openssl
    pkgs.opencl-headers
    pkgs.ocl-icd
    pkgs.glibcLocales
  ];
}
