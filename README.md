# presidents

## Requirements
- Python 3.7.0 (use Miniconda preferably)
- nodejs / npm
- vscode

## Linux Setup
### install required packages from pip and npm
```
npm run setup
```

### compile and hot-reload for development
```
npm run serve
```

### compile and minify for production
```
npm run build
```
## Windows Setup (not recommended)

### add conda to path
add the following to path; replace "...Miniconda3" with the path to your Miniconda directory
```
...Miniconda3
...Miniconda3\Scripts
...Miniconda3\Library\bin
```

### soften execution policy
run the following in an administrator Powershell
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned
```

### download build tools
download from [here](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

### installs required packages from pip and npm
```
npm run windows-setup
```

### modify launch.json
paste the following into your `launch.json`
```

```