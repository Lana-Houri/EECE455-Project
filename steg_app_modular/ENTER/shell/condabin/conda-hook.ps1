$Env:CONDA_EXE = "/home/amarus/ver4/steg_app_modular/ENTER/bin/conda"
$Env:_CONDA_EXE = "/home/amarus/ver4/steg_app_modular/ENTER/bin/conda"
$Env:_CE_M = $null
$Env:_CE_CONDA = $null
$Env:CONDA_PYTHON_EXE = "/home/amarus/ver4/steg_app_modular/ENTER/bin/python"
$Env:_CONDA_ROOT = "/home/amarus/ver4/steg_app_modular/ENTER"
$CondaModuleArgs = @{ChangePs1 = $True}

Import-Module "$Env:_CONDA_ROOT\shell\condabin\Conda.psm1" -ArgumentList $CondaModuleArgs

Remove-Variable CondaModuleArgs