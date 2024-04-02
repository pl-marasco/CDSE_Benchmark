s3fs sentinel-s2-l2a ~/AWS -o url=https://s3-eu-central-1.amazonaws.com -o endpoint=eu-central-1 -o sigv4 -o requester_pays

 s3fs eodata ~/CDSE -o passwd_file=${HOME}/.s3_CDSE_passwd -o url=https://eodata.dataspace.copernicus.eu/ -o use_path_request_style
 
 s3fs eodata ~/OTC -o passwd_file=${HOME}/.s3_CDSE_passwd -o url=https://eodata.ams.dataspace.copernicus.eu/ -o use_path_request_style