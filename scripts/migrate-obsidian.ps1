param(
  [string]$SourceRoot = "D:\obsidian\storage",
  [string]$DocsRoot = "C:\Users\a1921\Desktop\notes-main\docs"
)

$ErrorActionPreference = "Stop"

$imageExtensions = @(".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".avif", ".mp4")
$targetRootByTopLevel = @{
  "cs50"    = "计算机科学\cs50"
  "english" = "英文学习\Obsidian"
  "Math"    = "数学基础\Obsidian"
}

function Get-RelativePath([string]$FromDirectory, [string]$ToPath) {
  $fromUri = [Uri]((Resolve-Path -LiteralPath $FromDirectory).Path.TrimEnd("\") + "\")
  if (Test-Path -LiteralPath $ToPath) {
    $targetPath = (Resolve-Path -LiteralPath $ToPath).Path
  } else {
    $targetPath = $ToPath
  }
  $toUri = [Uri]$targetPath
  return [Uri]::UnescapeDataString($fromUri.MakeRelativeUri($toUri).ToString())
}

function Convert-ToUrlPath([string]$Path) {
  return ($Path -replace "\\", "/") -replace " ", "%20"
}

function Get-SafeFolderName([string]$RelativeMarkdownPath) {
  $withoutExtension = [IO.Path]::ChangeExtension($RelativeMarkdownPath, $null)
  $safe = $withoutExtension -replace '[<>:"/\\|?*]', "_"
  $safe = $safe -replace '\s+', "_"
  return $safe.Trim("_").TrimEnd(".")
}

function Get-SafeFileName([string]$FileName) {
  return ($FileName -replace '[<>:"/\\|?*]', "_").Trim("_")
}

function Resolve-Attachment([string]$Name, [string]$CurrentMarkdownDirectory) {
  $cleanName = ($Name -split "\|", 2)[0].Trim()
  $cleanName = [Uri]::UnescapeDataString($cleanName)
  $directCandidates = @(
    (Join-Path $CurrentMarkdownDirectory $cleanName),
    (Join-Path $SourceRoot $cleanName),
    (Join-Path $SourceRoot "photo\$cleanName")
  )

  foreach ($candidate in $directCandidates) {
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
      return (Resolve-Path -LiteralPath $candidate).Path
    }
  }

  $leaf = Split-Path -Leaf $cleanName
  $matches = Get-ChildItem -LiteralPath $SourceRoot -Recurse -File |
    Where-Object { $_.Name -eq $leaf }

  if ($matches.Count -gt 0) {
    return $matches[0].FullName
  }

  return $null
}

function Get-NoteHref([string]$LinkTarget, [string]$CurrentTargetMarkdown) {
  $target = ($LinkTarget -split "\|", 2)[0].Trim()
  if ($target -match "#") {
    $target = ($target -split "#", 2)[0].Trim()
  }
  if ([string]::IsNullOrWhiteSpace($target)) {
    return $null
  }

  $matched = $script:noteMapByStem[$target]
  if (-not $matched) {
    return $null
  }

  $fromDir = Split-Path -Parent $CurrentTargetMarkdown
  $relative = Get-RelativePath $fromDir $matched.Target
  return Convert-ToUrlPath $relative
}

$sourceMarkdownFiles = Get-ChildItem -LiteralPath $SourceRoot -Recurse -File -Filter *.md |
  Where-Object { $_.FullName -notmatch "\\\.obsidian\\" } |
  Sort-Object FullName

$script:noteMapByStem = @{}
$plannedNotes = @()

foreach ($file in $sourceMarkdownFiles) {
  $relative = Get-RelativePath $SourceRoot $file.FullName
  $parts = $relative -split "[/\\]"
  $topLevel = $parts[0]

  if (-not $targetRootByTopLevel.ContainsKey($topLevel)) {
    continue
  }

  $tail = ($parts | Select-Object -Skip 1) -join "\"
  $target = Join-Path $DocsRoot (Join-Path $targetRootByTopLevel[$topLevel] $tail)
  $planned = [PSCustomObject]@{
    Source = $file.FullName
    RelativeSource = $relative
    Target = $target
    ImageFolder = Join-Path $DocsRoot ("images\obsidian\" + (Get-SafeFolderName $relative))
  }
  $plannedNotes += $planned
  $script:noteMapByStem[[IO.Path]::GetFileNameWithoutExtension($file.Name)] = $planned
}

$warnings = New-Object System.Collections.Generic.List[string]
$copiedImages = 0

foreach ($note in $plannedNotes) {
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $note.Target) | Out-Null
  New-Item -ItemType Directory -Force -Path $note.ImageFolder | Out-Null

  $content = Get-Content -LiteralPath $note.Source -Raw -Encoding UTF8
  $currentSourceDir = Split-Path -Parent $note.Source
  $currentTargetDir = Split-Path -Parent $note.Target
  $assetFolder = Join-Path $DocsRoot ("assets\obsidian\" + (Get-SafeFolderName $note.RelativeSource))
  $imageState = [PSCustomObject]@{ Index = 0 }
  $imageMap = @{}
  $assetMap = @{}

  $content = [regex]::Replace($content, '!\[\[([^\]]+)\]\]', {
    param($match)
    $rawTarget = $match.Groups[1].Value
    $attachmentPath = Resolve-Attachment $rawTarget $currentSourceDir

    if (-not $attachmentPath) {
      $warnings.Add("Missing attachment: $($note.RelativeSource) -> $rawTarget")
      return $match.Value
    }

    $extension = [IO.Path]::GetExtension($attachmentPath).ToLowerInvariant()
    if (-not $imageExtensions.Contains($extension)) {
      if (-not $assetMap.ContainsKey($attachmentPath)) {
        New-Item -ItemType Directory -Force -Path $assetFolder | Out-Null
        $targetAsset = Join-Path $assetFolder (Get-SafeFileName (Split-Path -Leaf $attachmentPath))
        Copy-Item -LiteralPath $attachmentPath -Destination $targetAsset -Force
        $assetMap[$attachmentPath] = $targetAsset
      }

      $relativeAsset = Get-RelativePath $currentTargetDir $assetMap[$attachmentPath]
      $label = Split-Path -Leaf $attachmentPath
      return "[$label](" + (Convert-ToUrlPath $relativeAsset) + ")"
    }

    if (-not $imageMap.ContainsKey($attachmentPath)) {
      $imageState.Index += 1
      $newName = "img{0:D4}{1}" -f $imageState.Index, $extension
      $targetImage = Join-Path $note.ImageFolder $newName
      Copy-Item -LiteralPath $attachmentPath -Destination $targetImage -Force
      $imageMap[$attachmentPath] = $targetImage
      $script:copiedImages += 1
    }

    $relativeImage = Get-RelativePath $currentTargetDir $imageMap[$attachmentPath]
    return "![](" + (Convert-ToUrlPath $relativeImage) + ")"
  })

  $content = [regex]::Replace($content, '(?<!\!)\[\[([^\]]+)\]\]', {
    param($match)
    $rawTarget = $match.Groups[1].Value
    $attachmentPath = Resolve-Attachment $rawTarget $currentSourceDir

    if ($attachmentPath -and $imageExtensions.Contains([IO.Path]::GetExtension($attachmentPath).ToLowerInvariant())) {
      if (-not $imageMap.ContainsKey($attachmentPath)) {
        $imageState.Index += 1
        $newName = "img{0:D4}{1}" -f $imageState.Index, [IO.Path]::GetExtension($attachmentPath).ToLowerInvariant()
        $targetImage = Join-Path $note.ImageFolder $newName
        Copy-Item -LiteralPath $attachmentPath -Destination $targetImage -Force
        $imageMap[$attachmentPath] = $targetImage
        $script:copiedImages += 1
      }

      $relativeImage = Get-RelativePath $currentTargetDir $imageMap[$attachmentPath]
      return "![](" + (Convert-ToUrlPath $relativeImage) + ")"
    }

    if ($attachmentPath) {
      if (-not $assetMap.ContainsKey($attachmentPath)) {
        New-Item -ItemType Directory -Force -Path $assetFolder | Out-Null
        $targetAsset = Join-Path $assetFolder (Get-SafeFileName (Split-Path -Leaf $attachmentPath))
        Copy-Item -LiteralPath $attachmentPath -Destination $targetAsset -Force
        $assetMap[$attachmentPath] = $targetAsset
      }

      $relativeAsset = Get-RelativePath $currentTargetDir $assetMap[$attachmentPath]
      $label = Split-Path -Leaf $attachmentPath
      return "[$label](" + (Convert-ToUrlPath $relativeAsset) + ")"
    }

    $labelParts = $rawTarget -split "\|", 2
    $label = if ($labelParts.Count -eq 2) { $labelParts[1].Trim() } else { ($labelParts[0] -split "#", 2)[0].Trim() }
    $href = Get-NoteHref $rawTarget $note.Target

    if (-not $href) {
      $warnings.Add("Unresolved note link: $($note.RelativeSource) -> $rawTarget")
      return $label
    }

    return "[$label]($href)"
  })

  # Migrated notes use filenames as page titles, so demote Obsidian H1 sections.
  $content = [regex]::Replace($content, '(?m)^# ', '## ')

  Set-Content -LiteralPath $note.Target -Value $content -Encoding UTF8
}

$summary = [PSCustomObject]@{
  SourceRoot = $SourceRoot
  DocsRoot = $DocsRoot
  NotesMigrated = $plannedNotes.Count
  ImagesCopied = $copiedImages
  Warnings = $warnings.Count
}

$summary | Format-List
if ($warnings.Count -gt 0) {
  $warnings | Set-Content -LiteralPath (Join-Path $DocsRoot "images\obsidian\migration-warnings.txt") -Encoding UTF8
  Write-Host "Warnings written to docs\images\obsidian\migration-warnings.txt"
}
