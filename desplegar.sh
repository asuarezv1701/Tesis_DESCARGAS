#!/usr/bin/env bash
#
# desplegar.sh — Publica en GitHub los cambios del proyecto.
#
# Funciona igual en Tesis_ANALISIS y en Tesis_DESCARGAS: detecta la carpeta
# donde vive. Como son repositorios git independientes, hay que ejecutarlo
# dentro de cada uno por separado.
#
# IMPORTANTE: solo publica archivos que YA ESTAN versionados (git add -u).
# Los archivos nuevos se ignoran a proposito; si quieres incluir alguno,
# agregalo tu mismo antes:   git add ruta/al/archivo
#
# Uso:
#   ./desplegar.sh                     Commitea y sube (mensaje automatico)
#   ./desplegar.sh "mi mensaje"        Con tu propio mensaje
#   ./desplegar.sh --sin-push "msg"    Commit local, sin subir
#
set -euo pipefail

# ── Colores (se desactivan si la salida no es una terminal) ──────────────────
if [ -t 1 ]; then
  V=$'\033[92m'; A=$'\033[93m'; R=$'\033[91m'; B=$'\033[94m'; N=$'\033[0m'
else
  V=""; A=""; R=""; B=""; N=""
fi
ok()   { echo "${V}  OK${N}   $1"; }
warn() { echo "${A}  AVISO${N} $1"; }
err()  { echo "${R}  ERROR${N} $1"; }
tit()  { echo; echo "${B}=== $1 ===${N}"; }

cd "$(dirname "$0")"
RAIZ="$(pwd)"

# ── Argumentos ───────────────────────────────────────────────────────────────
HACER_PUSH=1
MENSAJE=""
for arg in "$@"; do
  case "$arg" in
    --sin-push) HACER_PUSH=0 ;;
    -h|--help)  sed -n '2,18p' "$0"; exit 0 ;;
    *)          MENSAJE="$arg" ;;
  esac
done

echo "${B}================================================================${N}"
echo "${B}  DESPLIEGUE — $(basename "$RAIZ")${N}"
echo "${B}================================================================${N}"

# ── 1. Comprobar que es un repositorio ───────────────────────────────────────
tit "1. Repositorio"
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  err "Esta carpeta no es un repositorio git."
  exit 1
fi
RAMA="$(git branch --show-current 2>/dev/null || echo 'HEAD')"
ok "Rama: $RAMA"

# ── 2. Ver que hay pendiente ─────────────────────────────────────────────────
tit "2. Cambios"

# Solo archivos YA versionados que fueron modificados o eliminados
MODIFICADOS="$(git diff --name-only)"
# Archivos nuevos que NO se subiran (informativo)
NUEVOS="$(git ls-files --others --exclude-standard)"

# Commits ya creados que faltan por publicar
SIN_PUBLICAR=0
POR_INTEGRAR=0
TIENE_REMOTO=0
if git remote get-url origin >/dev/null 2>&1; then
  TIENE_REMOTO=1
  git fetch origin --quiet 2>/dev/null || true
  if git rev-parse --verify --quiet "origin/$RAMA" >/dev/null 2>&1; then
    SIN_PUBLICAR=$(git rev-list --count "origin/$RAMA..HEAD" 2>/dev/null || echo 0)
    POR_INTEGRAR=$(git rev-list --count "HEAD..origin/$RAMA" 2>/dev/null || echo 0)
  fi
fi

if [ -n "$MODIFICADOS" ]; then
  echo "  Se publicaran estos archivos ya versionados:"
  echo "$MODIFICADOS" | sed 's/^/    /'
else
  echo "  Sin cambios en archivos versionados."
fi

if [ -n "$NUEVOS" ]; then
  echo
  warn "Archivos NUEVOS que NO se subiran (no estan versionados):"
  echo "$NUEVOS" | sed 's/^/    /'
  warn "Si quieres incluir alguno:  git add <archivo>  y vuelve a ejecutar."
fi

if [ "$SIN_PUBLICAR" -gt 0 ]; then
  echo
  echo "  Commits ya creados pendientes de publicar: $SIN_PUBLICAR"
fi

if [ -z "$MODIFICADOS" ] && [ "$SIN_PUBLICAR" -eq 0 ]; then
  echo
  warn "Nada que publicar."
  exit 0
fi

# ── 3. Commit ────────────────────────────────────────────────────────────────
tit "3. Commit"
if [ -z "$MODIFICADOS" ]; then
  ok "Sin cambios nuevos; se publicaran los commits ya existentes."
else
  # -u: solo archivos ya versionados (modificados o borrados).
  # Nunca agrega archivos nuevos.
  git add -u
  N_ARCH=$(git diff --cached --name-only | wc -l | tr -d ' ')
  if [ -z "$MENSAJE" ]; then
    MENSAJE="Actualizacion ($(date '+%Y-%m-%d %H:%M')) — ${N_ARCH} archivo(s)"
  fi
  git commit -q -m "$MENSAJE"
  ok "Commit creado: $(git log --oneline -1)"
  SIN_PUBLICAR=$((SIN_PUBLICAR + 1))
fi

# ── 4. Publicar ──────────────────────────────────────────────────────────────
tit "4. Publicacion"
if [ "$HACER_PUSH" -eq 0 ]; then
  warn "Se omitio el push (--sin-push). Pendientes: $SIN_PUBLICAR commit(s)."
  warn "Para subirlos:  git push origin $RAMA"
elif [ "$TIENE_REMOTO" -eq 0 ]; then
  warn "No hay remoto configurado; los commits quedan en local."
elif [ "$POR_INTEGRAR" -gt 0 ]; then
  err "El remoto tiene $POR_INTEGRAR commit(s) que no estan en tu copia local."
  err "Integralos primero:   git pull --rebase origin $RAMA"
  exit 1
elif git push -q origin "$RAMA" 2>/dev/null; then
  ok "Publicados $SIN_PUBLICAR commit(s) en origin/$RAMA"
else
  warn "No se pudo publicar (revisa conexion o credenciales)."
  warn "Reintenta con:  git push origin $RAMA"
fi

tit "Listo"
