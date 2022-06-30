if : >/dev/tcp/8.8.8.8/53; then
  echo 'Internet available.'
else
  echo 'Offline.'
fi
