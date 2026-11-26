# -*- coding: utf-8 -*-
"""Elementos finitos usados no estudo (numpy puro, sem dependências externas).

- Pórtico espacial de Euler-Bernoulli (2 nós, 12 GL: ux, uy, uz, rx, ry, rz)
- Treliça espacial (2 nós, só translações) — contraventamentos
- Placa de Mindlin-Reissner Q4 bilinear com integração seletiva reduzida
  (flexão 2×2 Gauss, cisalhamento 1 ponto) — evita travamento por cisalhamento em placas finas
Unidades consistentes: kN, m, kPa.
"""
import math
import numpy as np


# ============================================================ pórtico espacial
def eixos_locais(xi, xj, ref):
    ex = np.asarray(xj, float) - np.asarray(xi, float)
    L = np.linalg.norm(ex)
    ex /= L
    ref = np.asarray(ref, float)
    if abs(np.dot(ex, ref) / np.linalg.norm(ref)) > 0.999:
        ref = np.array([1.0, 0, 0]) if abs(ex[0]) < 0.9 else np.array([0, 1.0, 0])
    ez = np.cross(ex, ref)
    ez /= np.linalg.norm(ez)
    ey = np.cross(ez, ex)
    return np.vstack([ex, ey, ez]), L


def k_portico_local(E, G, A, Iy, Iz, J, L):
    """Rigidez local. Iz = inércia para flexão no plano x-y (eixo forte quando y = alma)."""
    k = np.zeros((12, 12))
    k[0, 0] = k[6, 6] = E * A / L
    k[0, 6] = k[6, 0] = -E * A / L
    k[3, 3] = k[9, 9] = G * J / L
    k[3, 9] = k[9, 3] = -G * J / L
    a, b, c, d = 12 * E * Iz / L ** 3, 6 * E * Iz / L ** 2, 4 * E * Iz / L, 2 * E * Iz / L
    for (i, j, v) in [(1, 1, a), (1, 5, b), (1, 7, -a), (1, 11, b), (5, 5, c), (5, 7, -b), (5, 11, d),
                      (7, 7, a), (7, 11, -b), (11, 11, c)]:
        k[i, j] = k[j, i] = v
    a, b, c, d = 12 * E * Iy / L ** 3, 6 * E * Iy / L ** 2, 4 * E * Iy / L, 2 * E * Iy / L
    for (i, j, v) in [(2, 2, a), (2, 4, -b), (2, 8, -a), (2, 10, -b), (4, 4, c), (4, 8, b), (4, 10, d),
                      (8, 8, a), (8, 10, b), (10, 10, c)]:
        k[i, j] = k[j, i] = v
    return k


def T12(R):
    T = np.zeros((12, 12))
    for i in range(4):
        T[3 * i:3 * i + 3, 3 * i:3 * i + 3] = R
    return T


def fef_uniforme(w_global, R, L):
    """Forças nodais equivalentes (sistema local) de carga uniforme w (kN/m, vetor global)."""
    wx, wy, wz = R @ np.asarray(w_global, float)
    return np.array([wx * L / 2, wy * L / 2, wz * L / 2, 0, -wz * L ** 2 / 12, wy * L ** 2 / 12,
                     wx * L / 2, wy * L / 2, wz * L / 2, 0, wz * L ** 2 / 12, -wy * L ** 2 / 12])


class Portico:
    """Modelo de pórtico espacial com elementos de barra e treliça."""

    def __init__(self):
        self.X = []          # coordenadas dos nós
        self.el = []         # dicts: i, j, tipo('frame'|'truss'), props, ref, grupo, ativo
        self.apoios = {}     # nó -> lista de GL restritos (0..5)

    def no(self, x, y, z, tol=1e-6):
        p = np.array([x, y, z], float)
        for k, q in enumerate(self.X):
            if np.linalg.norm(q - p) < tol:
                return k
        self.X.append(p)
        return len(self.X) - 1

    def barra(self, i, j, props, ref=(0, 0, 1), grupo="", tipo="frame"):
        self.el.append(dict(i=i, j=j, p=props, ref=ref, grupo=grupo, tipo=tipo, ativo=True))
        return len(self.el) - 1

    def ndof(self):
        return 6 * len(self.X)

    def k_el(self, e):
        Xi, Xj = self.X[e["i"]], self.X[e["j"]]
        R, L = eixos_locais(Xi, Xj, e["ref"])
        p = e["p"]
        if e["tipo"] == "truss":
            kl = np.zeros((12, 12))
            kl[0, 0] = kl[6, 6] = p["E"] * p["A"] / L
            kl[0, 6] = kl[6, 0] = -p["E"] * p["A"] / L
        else:
            kl = k_portico_local(p["E"], p["G"], p["A"], p["Iy"], p["Iz"], p["J"], L)
        return kl, R, L

    def montar_K(self):
        n = self.ndof()
        K = np.zeros((n, n))
        cache = []
        for e in self.el:
            kl, R, L = self.k_el(e)
            T = T12(R)
            cache.append((kl, R, L, T))
            if not e["ativo"]:
                continue
            kg = T.T @ kl @ T
            idx = np.r_[6 * e["i"]:6 * e["i"] + 6, 6 * e["j"]:6 * e["j"] + 6]
            K[np.ix_(idx, idx)] += kg
        return K, cache

    def resolver(self, F_nodal, w_el, cache_K=None):
        """F_nodal: vetor global; w_el: dict el -> vetor w global (kN/m)."""
        K, cache = cache_K if cache_K else self.montar_K()
        F = F_nodal.copy()
        fef = {}
        for ie, w in w_el.items():
            kl, R, L, T = cache[ie]
            fl = fef_uniforme(w, R, L)
            fef[ie] = fl
            idx = np.r_[6 * self.el[ie]["i"]:6 * self.el[ie]["i"] + 6, 6 * self.el[ie]["j"]:6 * self.el[ie]["j"] + 6]
            F[idx] += T.T @ fl
        fix = sorted({6 * n + d for n, ds in self.apoios.items() for d in ds})
        # GL de rotação sem rigidez (nós só de treliça) recebem mola numérica desprezível
        diag = np.diag(K).copy()
        livres = [i for i in range(len(F)) if i not in set(fix)]
        Kff = K[np.ix_(livres, livres)].copy()
        for a, i in enumerate(livres):
            if diag[i] == 0:
                Kff[a, a] = 1e-6
        u = np.zeros(len(F))
        u[livres] = np.linalg.solve(Kff, F[livres])
        Rv = K @ u - F
        esf = []
        for ie, e in enumerate(self.el):
            kl, R, L, T = cache[ie]
            idx = np.r_[6 * e["i"]:6 * e["i"] + 6, 6 * e["j"]:6 * e["j"] + 6]
            ul = T @ u[idx]
            f = kl @ ul - fef.get(ie, np.zeros(12)) if e["ativo"] else np.zeros(12)
            esf.append(f)
        return u, Rv, esf, fix

    def massa_lumped(self, m_nodal_extra, rho):
        n = self.ndof()
        M = np.zeros(n)
        for e in self.el:
            _, L = eixos_locais(self.X[e["i"]], self.X[e["j"]], e["ref"])
            m = rho * e["p"]["A"] * L / 2
            for nd in (e["i"], e["j"]):
                M[6 * nd:6 * nd + 3] += m
        for nd, m in m_nodal_extra.items():
            M[6 * nd:6 * nd + 3] += m
        for nd in range(len(self.X)):
            M[6 * nd + 3:6 * nd + 6] += 1e-4   # inércia rotacional desprezível (evita singularidade)
        return M

    def modal(self, M, nmodos=6):
        K, _ = self.montar_K()
        fix = set(6 * n + d for n, ds in self.apoios.items() for d in ds)
        livres = [i for i in range(self.ndof()) if i not in fix]
        Kf = K[np.ix_(livres, livres)]
        for a, i in enumerate(livres):
            if Kf[a, a] == 0:
                Kf[a, a] = 1e-6
        mf = M[livres]
        Dm = 1 / np.sqrt(mf)
        A = Dm[:, None] * Kf * Dm[None, :]
        w2, V = np.linalg.eigh(A)
        ordem = np.argsort(w2)
        out = []
        for k in ordem[:nmodos]:
            phi = np.zeros(self.ndof())
            phi[livres] = Dm * V[:, k]
            out.append((math.sqrt(max(w2[k], 0)) / (2 * math.pi), phi))
        return out


# ============================================================ placa Mindlin Q4
def _dN(xi, eta):
    N = 0.25 * np.array([(1 - xi) * (1 - eta), (1 + xi) * (1 - eta), (1 + xi) * (1 + eta), (1 - xi) * (1 + eta)])
    dxi = 0.25 * np.array([-(1 - eta), (1 - eta), (1 + eta), -(1 + eta)])
    deta = 0.25 * np.array([-(1 - xi), -(1 + xi), (1 + xi), (1 - xi)])
    return N, dxi, deta


def k_mindlin(xy, E, nu, t, kappa=5 / 6):
    """Rigidez 12×12 (GL por nó: w, βx, βy — inclinações) de placa de Mindlin, integração seletiva."""
    Db = E * t ** 3 / (12 * (1 - nu ** 2)) * np.array([[1, nu, 0], [nu, 1, 0], [0, 0, (1 - nu) / 2]])
    Gs = kappa * E / (2 * (1 + nu)) * t
    K = np.zeros((12, 12))
    g = 1 / math.sqrt(3)

    def jac(xi, eta):
        N, dxi, deta = _dN(xi, eta)
        J = np.array([[dxi @ xy[:, 0], dxi @ xy[:, 1]], [deta @ xy[:, 0], deta @ xy[:, 1]]])
        dxy = np.linalg.solve(J, np.vstack([dxi, deta]))
        return N, dxy, np.linalg.det(J)

    for xi in (-g, g):
        for eta in (-g, g):
            N, dxy, dJ = jac(xi, eta)
            Bb = np.zeros((3, 12))
            for a in range(4):
                # GL (w, βx, βy) com β = inclinações: κx = βx,x ; κy = βy,y ; κxy = βx,y + βy,x
                Bb[0, 3 * a + 1] = dxy[0, a]
                Bb[1, 3 * a + 2] = dxy[1, a]
                Bb[2, 3 * a + 1] = dxy[1, a]
                Bb[2, 3 * a + 2] = dxy[0, a]
            K += Bb.T @ Db @ Bb * dJ
    N, dxy, dJ = jac(0, 0)
    Bs = np.zeros((2, 12))
    for a in range(4):
        # γx = w,x − βx ; γy = w,y − βy
        Bs[0, 3 * a] = dxy[0, a]
        Bs[0, 3 * a + 1] = -N[a]
        Bs[1, 3 * a] = dxy[1, a]
        Bs[1, 3 * a + 2] = -N[a]
    K += Bs.T @ (Gs * np.eye(2)) @ Bs * dJ * 4.0
    return K, Db


def momentos_centro(xy, ue, Db):
    """Momentos (Mx, My, Mxy) no centro do elemento (kN·m/m); M > 0 traciona a face inferior."""
    N, dxi, deta = _dN(0, 0)
    J = np.array([[dxi @ xy[:, 0], dxi @ xy[:, 1]], [deta @ xy[:, 0], deta @ xy[:, 1]]])
    dxy = np.linalg.solve(J, np.vstack([dxi, deta]))
    Bb = np.zeros((3, 12))
    for a in range(4):
        Bb[0, 3 * a + 1] = dxy[0, a]
        Bb[1, 3 * a + 2] = dxy[1, a]
        Bb[2, 3 * a + 1] = dxy[1, a]
        Bb[2, 3 * a + 2] = dxy[0, a]
    return Db @ (Bb @ ue)   # convenção: M > 0 traciona a face inferior (w positivo para cima)


class PlacaRet:
    """Malha retangular estruturada de placa de Mindlin (linhas de malha xs, ys)."""

    def __init__(self, xs, ys, E, nu, t):
        self.xs, self.ys = np.asarray(xs), np.asarray(ys)
        self.nx, self.ny = len(xs), len(ys)
        self.E, self.nu, self.t = E, nu, t
        self.elems = []
        for j in range(self.ny - 1):
            for i in range(self.nx - 1):
                n0 = j * self.nx + i
                self.elems.append([n0, n0 + 1, n0 + 1 + self.nx, n0 + self.nx])
        self.nn = self.nx * self.ny

    def coord(self, n):
        return self.xs[n % self.nx], self.ys[n // self.nx]

    def resolver(self, q_fun, molas_w=None, fix_w=(), fix_all=(), cargas_nodais=None):
        """q_fun(x,y) -> pressão (kPa, positiva para baixo). molas_w: k (kN/m³) Winkler."""
        n = 3 * self.nn
        K = np.zeros((n, n))
        F = np.zeros(n)
        self._Db = None
        for el in self.elems:
            xy = np.array([self.coord(a) for a in el])
            ke, Db = k_mindlin(xy, self.E, self.nu, self.t)
            self._Db = Db
            idx = np.array([[3 * a, 3 * a + 1, 3 * a + 2] for a in el]).ravel()
            K[np.ix_(idx, idx)] += ke
            area = (xy[1, 0] - xy[0, 0]) * (xy[3, 1] - xy[0, 1])
            xc, yc = xy[:, 0].mean(), xy[:, 1].mean()
            q = q_fun(xc, yc)
            for a in el:
                F[3 * a] -= q * area / 4
                if molas_w:
                    K[3 * a, 3 * a] += molas_w * area / 4
        if cargas_nodais:
            for a, P in cargas_nodais.items():
                F[3 * a] -= P
        fix = set()
        for a in fix_w:
            fix.add(3 * a)
        for a in fix_all:
            fix |= {3 * a, 3 * a + 1, 3 * a + 2}
        livres = np.array([i for i in range(n) if i not in fix])
        u = np.zeros(n)
        u[livres] = np.linalg.solve(K[np.ix_(livres, livres)], F[livres])
        M = []
        for el in self.elems:
            xy = np.array([self.coord(a) for a in el])
            idx = np.array([[3 * a, 3 * a + 1, 3 * a + 2] for a in el]).ravel()
            M.append(momentos_centro(xy, u[idx], self._Db))
        return u, np.array(M)
