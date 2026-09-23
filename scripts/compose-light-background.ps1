param(
  [Parameter(Mandatory)][string]$Original,
  [Parameter(Mandatory)][string]$GeneratedPatch,
  [Parameter(Mandatory)][string]$Output
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$source = [System.Drawing.Bitmap]::new((Resolve-Path -LiteralPath $Original).Path)
$generated = [System.Drawing.Bitmap]::new((Resolve-Path -LiteralPath $GeneratedPatch).Path)
$overlap = [int][Math]::Floor($source.Width * .1)
$width = $source.Height * 2
$extension = $width - $source.Width
$patch = [System.Drawing.Bitmap]::new($extension + $overlap, $source.Height)
$canvas = [System.Drawing.Bitmap]::new($width, $source.Height)
try {
  $graphics = [System.Drawing.Graphics]::FromImage($patch)
  $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $graphics.DrawImage($generated, [System.Drawing.Rectangle]::new(0, 0, $patch.Width, $patch.Height))
  $graphics.Dispose()
  $graphics = [System.Drawing.Graphics]::FromImage($canvas)
  $graphics.DrawImageUnscaled($patch, 0, 0)
  $graphics.DrawImageUnscaled($source, $extension, 0)
  $graphics.Dispose()
  # Blend only inside the authorized leftmost 10%; every other original pixel stays intact.
  # Keep the reference's small floating petal intact, rather than ghosting it
  # with a second generated petal. The blend occupies only the first third.
  $blendWidth = [int][Math]::Floor($overlap / 3)
  for ($x = 0; $x -lt $blendWidth; $x++) {
    $t = $x / ($blendWidth - 1)
    $weight = $t * $t * (3 - 2 * $t)
    for ($y = 0; $y -lt $source.Height; $y++) {
      $a = $patch.GetPixel($extension + $x, $y)
      $b = $source.GetPixel($x, $y)
      $canvas.SetPixel($extension + $x, $y, [System.Drawing.Color]::FromArgb(
        [int][Math]::Round($a.R * (1 - $weight) + $b.R * $weight),
        [int][Math]::Round($a.G * (1 - $weight) + $b.G * $weight),
        [int][Math]::Round($a.B * (1 - $weight) + $b.B * $weight)))
    }
  }
  $canvas.Save($Output, [System.Drawing.Imaging.ImageFormat]::Png)
  # Compare lossless encodings of the untouched 90%, not a perceptual approximation.
  $before = $source.Clone([System.Drawing.Rectangle]::new($overlap, 0, $source.Width - $overlap, $source.Height), [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
  $after = $canvas.Clone([System.Drawing.Rectangle]::new($extension + $overlap, 0, $source.Width - $overlap, $source.Height), [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
  $hashes = foreach ($bitmap in @($before, $after)) {
    $stream = [System.IO.MemoryStream]::new()
    $bitmap.Save($stream, [System.Drawing.Imaging.ImageFormat]::Png)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    [Convert]::ToBase64String($sha.ComputeHash($stream.ToArray()))
    $sha.Dispose(); $stream.Dispose(); $bitmap.Dispose()
  }
  if ($hashes[0] -ne $hashes[1]) { throw 'Original pixel preservation check failed.' }
  Write-Output "Saved ${width}x$($source.Height); right 90% original pixels verified identical."
} finally {
  $source.Dispose(); $generated.Dispose(); $patch.Dispose(); $canvas.Dispose()
}
