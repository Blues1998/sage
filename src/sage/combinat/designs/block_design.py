"""
Block designs.

A module to help with constructions and computations of block
designs and other incidence structures.

A block design is an incidence structure consisting of a set of points `P` and a
set of blocks `B`, where each block is considered as a subset of `P`. More
precisely, a *block design* `B` is a class of `k`-element subsets of `P` such
that the number `r` of blocks that contain any point `x` in `P` is independent
of `x`, and the number `\lambda` of blocks that contain any given `t`-element
subset `T` is independent of the choice of `T` (see [1]_ for more). Such a block
design is also called a `t-(v,k,\lambda)`-design, and `v` (the number of
points), `b` (the number of blocks), `k`, `r`, and `\lambda` are the parameters
of the design. (In Python, ``lambda`` is reserved, so we sometimes use ``lmbda``
or ``L`` instead.)

In Sage, sets are replaced by (ordered) lists and the standard representation of
a block design uses `P = [0,1,..., v-1]`, so a block design is specified by
`(v,B)`.

REFERENCES:

.. [1] Block design from wikipedia,
  :wikipedia:`Block_design`

.. [2] What is a block design?,
  http://designtheory.org/library/extrep/extrep-1.1-html/node4.html (in 'The
  External Representation of Block Designs' by Peter J. Cameron, Peter
  Dobcsanyi, John P. Morgan, Leonard H. Soicher)

.. [We07] Charles Weibel, "Survey of Non-Desarguesian planes" (2007), notices of
   the AMS, vol. 54 num. 10, pages 1294--1303

AUTHORS:

- Vincent Delecroix (2014): rewrite the part on projective planes :trac:`16281`

- Peter Dobcsanyi and David Joyner (2007-2008)

  This is a significantly modified form of the module block_design.py (version
  0.6) written by Peter Dobcsanyi peter@designtheory.org. Thanks go to Robert
  Miller for lots of good design suggestions.

.. TODO::

    Implement finite non-Desarguesian plane as in [We07]_ and
    :wikipedia:`Non-Desarguesian_plane`.

Functions and methods
---------------------
"""
#***************************************************************************
#                              Copyright (C) 2007                          #
#                                                                          #
#                Peter Dobcsanyi       and         David Joyner            #
#           <peter@designtheory.org>          <wdjoyner@gmail.com>         #
#                                                                          #
#                                                                          #
#    Distributed under the terms of the GNU General Public License (GPL)   #
#    as published by the Free Software Foundation; either version 2 of     #
#    the License, or (at your option) any later version.                   #
#                    http://www.gnu.org/licenses/                          #
#***************************************************************************

from sage.modules.free_module import VectorSpace
from sage.rings.integer_ring import ZZ
from sage.rings.arith import binomial, integer_floor
from sage.combinat.designs.incidence_structures import IncidenceStructure, IncidenceStructureFromMatrix
from sage.misc.decorators import rename_keyword
from sage.rings.finite_rings.constructor import FiniteField
from sage.categories.sets_cat import EmptySetError
from sage.misc.unknown import Unknown

###  utility functions  -------------------------------------------------------

def tdesign_params(t, v, k, L):
    """
    Return the design's parameters: `(t, v, b, r , k, L)`. Note that `t` must be
    given.

    EXAMPLES::

        sage: BD = BlockDesign(7,[[0,1,2],[0,3,4],[0,5,6],[1,3,5],[1,4,6],[2,3,6],[2,4,5]])
        sage: from sage.combinat.designs.block_design import tdesign_params
        sage: tdesign_params(2,7,3,1)
        (2, 7, 7, 3, 3, 1)
    """
    x = binomial(v, t)
    y = binomial(k, t)
    b = divmod(L * x, y)[0]
    x = binomial(v-1, t-1)
    y = binomial(k-1, t-1)
    r = integer_floor(L * x/y)
    return (t, v, b, r, k, L)

def ProjectiveGeometryDesign(n, d, F, algorithm=None):
    """
    Returns a projective geometry design.

    A projective geometry design of parameters `n,d,F` has for points the lines
    of `F^{n+1}`, and for blocks the `d+1`-dimensional subspaces of `F^{n+1}`,
    each of which contains `\\frac {|F|^{d+1}-1} {|F|-1}` lines.

    INPUT:

    - ``n`` is the projective dimension

    - ``d`` is the dimension of the subspaces of `P = PPn(F)` which
      make up the blocks.

    - ``F`` is a finite field.

    - ``algorithm`` -- set to ``None`` by default, which results in using Sage's
      own implementation. In order to use GAP's implementation instead (i.e. its
      ``PGPointFlatBlockDesign`` function) set ``algorithm="gap"``. Note that
      GAP's "design" package must be available in this case, and that it can be
      installed with the ``gap_packages`` spkg.

    EXAMPLES:

    The points of the following design are the `\\frac {2^{2+1}-1} {2-1}=7`
    lines of `\mathbb{Z}_2^{2+1}`. It has `7` blocks, corresponding to each
    2-dimensional subspace of `\mathbb{Z}_2^{2+1}`::

        sage: designs.ProjectiveGeometryDesign(2, 1, GF(2))
        Incidence structure with 7 points and 7 blocks
        sage: BD = designs.ProjectiveGeometryDesign(2, 1, GF(2), algorithm="gap") # optional - gap_packages (design package)
        sage: BD.is_block_design()                                     # optional - gap_packages (design package)
        (True, [2, 7, 3, 1])
    """
    q = F.order()
    from sage.interfaces.gap import gap, GapElement
    from sage.sets.set import Set
    if algorithm is None:
        V = VectorSpace(F, n+1)
        points = list(V.subspaces(1))
        flats = list(V.subspaces(d+1))
        blcks = []
        for p in points:
            b = []
            for i in range(len(flats)):
                if p.is_subspace(flats[i]):
                    b.append(i)
            blcks.append(b)
        v = (q**(n+1)-1)/(q-1)
        return BlockDesign(v, blcks, name="ProjectiveGeometryDesign")
    if algorithm == "gap":   # Requires GAP's Design
        gap.load_package("design")
        gap.eval("D := PGPointFlatBlockDesign( %s, %s, %d )"%(n,q,d))
        v = eval(gap.eval("D.v"))
        gblcks = eval(gap.eval("D.blocks"))
        gB = []
        for b in gblcks:
            gB.append([x-1 for x in b])
        return BlockDesign(v, gB, name="ProjectiveGeometryDesign")

def DesarguesianProjectivePlaneDesign(n, check=True):
    r"""
    Return the Desarguesian projective plane of order ``n`` as a 2-design.

    INPUT:

    - ``n`` -- an integer which must be a power of a prime number

    - ``check`` -- (boolean) Whether to check that output is correct before
      returning it. As this is expected to be useless (but we are cautious
      guys), you may want to disable it whenever you want speed. Set to
      ``True`` by default.

    .. SEEALSO::

        :func:`ProjectiveGeometryDesign`

    EXAMPLES::

        sage: designs.DesarguesianProjectivePlaneDesign(2)
        Incidence structure with 7 points and 7 blocks
        sage: designs.DesarguesianProjectivePlaneDesign(3)
        Incidence structure with 13 points and 13 blocks
        sage: designs.DesarguesianProjectivePlaneDesign(4)
        Incidence structure with 21 points and 21 blocks
        sage: designs.DesarguesianProjectivePlaneDesign(5)
        Incidence structure with 31 points and 31 blocks
        sage: designs.DesarguesianProjectivePlaneDesign(6)
        Traceback (most recent call last):
        ...
        ValueError: the order of a finite field must be a prime power.
    """
    K = FiniteField(n, 'x')
    n2 = n**2
    relabel = {x:i for i,x in enumerate(K)}
    Kiter = relabel  # it is much faster to iterate throug a dict than through
                     # the finite field K

    # we relabel the points in the projective plane as follows
    # (x,y,1) -> relabel[x] + n*relabel[y]
    # (x,1,0) -> n^2 + relabel[x]
    # (1,0,0) -> n^2 + n

    blcks = []

    # build the lines n^2 lines x = sy + az
    for s in Kiter:
        for a in Kiter:
            # the point in the affine plane (z=1)
            blcks.append([relabel[s*y+a] + n*relabel[y] for y in Kiter])
            # add the point at infinity (z=0)
            blcks[-1].append(n2 + relabel[s])

    # build the n horizontals y = az
    for a in Kiter:
        # the point in the affine plane (z=1)
        blcks.append([relabel[x] + n*relabel[a] for x in Kiter])
        # the point at infinity is (1:0:0)
        blcks[-1].append(n2 + n)

    # build the line at infinity x=0
    blcks.append([n2 + i for i in xrange(n+1)])

    return BlockDesign(n2+n+1, blcks, name="Desarguesian projective plane of order %d"%n, test=check)

def projective_plane_to_OA(pplane, pt=None, check=True):
    r"""
    Return the orthogonal array built from the projective plane ``pplane`.

    The orthogonal array `OA(n+1,n,2)` is obtained from the projective plane
    ``pplane`` by removing the point ``pt`` and the `n+1` lines that pass
    through it`. These `n+1` lines form the `n+1` groups while the remaining
    `n^2+n` lines form the transversals.

    INPUT:

    - ``pplane`` - a projective plane as a 2-design

    - ``pt`` - a point in the projective plane ``pplane``

    - ``check`` -- (boolean) Whether to check that output is correct before
      returning it. As this is expected to be useless (but we are cautious
      guys), you may want to disable it whenever you want speed. Set to
      ``True`` by default.

    .. SEEALSO:

        The function :func:`OA_to_projective_plane` does the reverse operation.
        For more on orthogonal arrays, you may have a look at
        :func:`~sage.combinat.designs.orthogonal_arrays.orthogonal_array`

    EXAMPLES::

        sage: from sage.combinat.designs.block_design import projective_plane_to_OA
        sage: p2 = designs.DesarguesianProjectivePlaneDesign(2)
        sage: projective_plane_to_OA(p2)
        [[0, 0, 0], [0, 1, 1], [1, 0, 1], [1, 1, 0]]
        sage: p3 = designs.DesarguesianProjectivePlaneDesign(3)
        sage: projective_plane_to_OA(p3)
        [[0, 0, 0, 0],
         [0, 1, 2, 1],
         [0, 2, 1, 2],
         [1, 0, 2, 2],
         [1, 1, 1, 0],
         [1, 2, 0, 1],
         [2, 0, 1, 1],
         [2, 1, 0, 2],
         [2, 2, 2, 0]]

        sage: pp = designs.DesarguesianProjectivePlaneDesign(16)
        sage: _ = projective_plane_to_OA(pp, pt=0)
        sage: _ = projective_plane_to_OA(pp, pt=3)
        sage: _ = projective_plane_to_OA(pp, pt=7)
    """
    n = len(pplane.blcks[0]) - 1

    assert len(pplane.blcks) == n**2+n+1, "pplane is not a projective plane"

    if pt is None:
        pt = n**2+n

    # make the list of the lines that pass through the point pt
    L = []
    OA = []
    for blk in pplane.blcks:
        assert len(blk) == n+1, "pplane is not a projective plane"
        if pt in blk:
            b = blk[:]
            b.remove(pt)
            L.append(b)
        else:
            OA.append(blk)

    assert len(L) == n+1, "pplane is not a projective plane"

    # relabel to fit with the convention of orthogonal array: each line that
    # pass through the point ``pt`` must have their points labeled from 0 to n-1
    relabel = dict((x,(j,i)) for j,l in enumerate(L) for i,x in enumerate(l))
    OA = [sorted(relabel[x] for x in l) for l in OA]
    OA = [[x[1] for x in l] for l in OA]

    if check:
        from orthogonal_arrays import is_orthogonal_array
        is_orthogonal_array(OA,n+1,n,2)

    return OA

def OA_to_projective_plane(OA, check=True):
    r"""
    Return the projective plane associated to an `OA(n+1,n,2)`.

    .. SEEALSO::

        :func:`projective_plane_to_OA` for the function that goes the other way
        around.

    EXAMPLES::

        sage: from sage.combinat.designs.block_design import projective_plane_to_OA
        sage: from sage.combinat.designs.block_design import OA_to_projective_plane
        sage: p3 = designs.DesarguesianProjectivePlaneDesign(3)
        sage: OA3 = projective_plane_to_OA(p3)
        sage: OA_to_projective_plane(OA3)
        Incidence structure with 13 points and 13 blocks

        sage: p4 = designs.DesarguesianProjectivePlaneDesign(4)
        sage: OA4 = projective_plane_to_OA(p4)
        sage: OA_to_projective_plane(OA4)
        Incidence structure with 21 points and 21 blocks
    """
    n = len(OA[0])-1
    n2 = n**2

    assert len(OA) == n2, "the orthogonal array does not have parameters k=n+1,t=2"

    blcks = []

    # add the n^2 lines that correspond to transversals
    for l in OA:
        blcks.append([i+(n+1)*j for i,j in enumerate(l)])

    # add the n+1 lines that correspond to transversals
    for i in xrange(n+1):
        blcks.append(range(i*n, (i+1)*n))
        blcks[-1].append(n2+n)

    return BlockDesign(n2+n+1, blcks, name="Projective plane of order %d (built from an OA(%d,%d,2))"%(n,n+1,n), test=check)

def projective_plane(n):
    r"""
    Returns a projective plane of order ``n`` as a 2-design.

    A finite projective plane is a 2-design with `n^2+n+1` lines (or blocks) and
    `n^2+n+1` points. For more information on finite projective planes, see the
    :wikipedia:`Projective_plane#Finite_projective_planes`.

    If no construction is possible, then the function raises a ``EmptySetError``
    whereas if no construction is available the function raises a
    ``NotImplementedError``.

    INPUT:

    - ``n`` -- the finite projective plane's order

    EXAMPLES::

        sage: designs.projective_plane(2)
        Incidence structure with 7 points and 7 blocks
        sage: designs.projective_plane(3)
        Incidence structure with 13 points and 13 blocks
        sage: designs.projective_plane(4)
        Incidence structure with 21 points and 21 blocks
        sage: designs.projective_plane(5)
        Incidence structure with 31 points and 31 blocks
        sage: designs.projective_plane(6)
        Traceback (most recent call last):
        ...
        EmptySetError: By the Ryser-Chowla theorem, no projective plane of order 6 exists.
        sage: designs.projective_plane(10)
        Traceback (most recent call last):
        ...
        EmptySetError: No projective plane of order 10 exists by C. Lam, L. Thiel and S. Swiercz "The nonexistence of finite projective planes of order 10" (1989), Canad. J. Math.
        sage: designs.projective_plane(12)
        Traceback (most recent call last):
        ...
        NotImplementedError: If such a projective plane exists, we do not know how to build it.
        sage: designs.projective_plane(14)
        Traceback (most recent call last):
        ...
        EmptySetError: By the Ryser-Chowla theorem, no projective plane of order 14 exists.
    """
    from sage.rings.arith import is_prime_power, two_squares

    if n <= 1:
        raise EmptySetError("There is no projective plane of order <= 1")

    if n == 10:
        ref = ("C. Lam, L. Thiel and S. Swiercz \"The nonexistence of finite "
               "projective planes of order 10\" (1989), Canad. J. Math.")
        raise EmptySetError("No projective plane of order 10 exists by %s"%ref)

    if (n%4) in [1,2]:
        try:
            two_squares(n)
        except ValueError:
            raise EmptySetError("By the Ryser-Chowla theorem, no projective"
                         " plane of order "+str(n)+" exists.")

    if not is_prime_power(n):
        raise NotImplementedError("If such a projective plane exists, we do "
                                  "not know how to build it.")

    return DesarguesianProjectivePlaneDesign(n)


def AffineGeometryDesign(n, d, F):
    r"""
    Returns an Affine Geometry Design.

    INPUT:

    - `n` (integer) -- the Euclidean dimension. The number of points is
      `v=|F^n|`.

    - `d` (integer) -- the dimension of the (affine) subspaces of `P = GF(q)^n`
      which make up the blocks.

    - `F` -- a Finite Field (i.e. ``FiniteField(17)``), or a prime power
      (i.e. an integer)

    `AG_{n,d} (F)`, as it is sometimes denoted, is a `2` - `(v, k, \lambda)`
    design of points and `d`- flats (cosets of dimension `n`) in the affine
    geometry `AG_n (F)`, where

    .. math::

             v = q^n,\  k = q^d ,
             \lambda =\frac{(q^{n-1}-1) \cdots (q^{n+1-d}-1)}{(q^{n-1}-1) \cdots (q-1)}.

    Wraps some functions used in GAP Design's ``PGPointFlatBlockDesign``.  Does
    *not* require GAP's Design package.

    EXAMPLES::

        sage: BD = designs.AffineGeometryDesign(3, 1, GF(2))
        sage: BD.parameters(t=2)
        (2, 8, 2, 1)
        sage: BD.is_block_design()
        (True, [2, 8, 2, 1])
        sage: BD = designs.AffineGeometryDesign(3, 2, GF(2))
        sage: BD.parameters(t=3)
        (3, 8, 4, 1)
        sage: BD.is_block_design()
        (True, [3, 8, 4, 1])

    A 3-design::

        sage: D = IncidenceStructure(range(32),designs.steiner_quadruple_system(32))
        sage: D.is_block_design()
        (True, [3, 32, 4, 1])

    With an integer instead of a Finite Field::

        sage: BD = designs.AffineGeometryDesign(3, 2, 4)
        sage: BD.parameters(t=2)
        (2, 64, 16, 5)
    """
    try:
        q = int(F)
    except TypeError:
        q = F.order()

    from sage.interfaces.gap import gap, GapElement
    from sage.sets.set import Set
    gap.eval("V:=GaloisField(%s)^%s"%(q,n))
    gap.eval("points:=AsSet(V)")
    gap.eval("Subs:=AsSet(Subspaces(V,%s));"%d)
    gap.eval("CP:=Cartesian(points,Subs)")
    flats = gap.eval("flats:=List(CP,x->Sum(x))") # affine spaces
    gblcks = eval(gap.eval("Set(List(flats,f->Filtered([1..Length(points)],i->points[i] in f)));"))
    v = q**n
    gB = []
    for b in gblcks:
       gB.append([x-1 for x in b])
    return BlockDesign(v, gB, name="AffineGeometryDesign")

def WittDesign(n):
    """
    INPUT:

    - ``n`` is in `9,10,11,12,21,22,23,24`.

    Wraps GAP Design's WittDesign. If ``n=24`` then this function returns the
    large Witt design `W_{24}`, the unique (up to isomorphism) `5-(24,8,1)`
    design. If ``n=12`` then this function returns the small Witt design
    `W_{12}`, the unique (up to isomorphism) `5-(12,6,1)` design.  The other
    values of `n` return a block design derived from these.

    .. NOTE:

        Requires GAP's Design package (included in the gap_packages Sage spkg).

    EXAMPLES::

        sage: BD = designs.WittDesign(9)   # optional - gap_packages (design package)
        sage: BD.is_block_design()      # optional - gap_packages (design package)
        (True, [2, 9, 3, 1])
        sage: BD                   # optional - gap_packages (design package)
        Incidence structure with 9 points and 12 blocks
        sage: print BD             # optional - gap_packages (design package)
        WittDesign<points=[0, 1, 2, 3, 4, 5, 6, 7, 8], blocks=[[0, 1, 7], [0, 2, 5], [0, 3, 4], [0, 6, 8], [1, 2, 6], [1, 3, 5], [1, 4, 8], [2, 3, 8], [2, 4, 7], [3, 6, 7], [4, 5, 6], [5, 7, 8]]>
        sage: BD = designs.WittDesign(12)  # optional - gap_packages (design package)
        sage: BD.is_block_design()         # optional - gap_packages (design package)
        (True, [5, 12, 6, 1])
    """
    from sage.interfaces.gap import gap, GapElement
    gap.load_package("design")
    gap.eval("B:=WittDesign(%s)"%n)
    v = eval(gap.eval("B.v"))
    gblcks = eval(gap.eval("B.blocks"))
    gB = []
    for b in gblcks:
       gB.append([x-1 for x in b])
    return BlockDesign(v, gB, name="WittDesign", test=True)

def HadamardDesign(n):
    """
    As described in Section 1, p. 10, in [CvL]. The input n must have the
    property that there is a Hadamard matrix of order `n+1` (and that a
    construction of that Hadamard matrix has been implemented...).

    EXAMPLES::

        sage: designs.HadamardDesign(7)
        Incidence structure with 7 points and 7 blocks
        sage: print designs.HadamardDesign(7)
        HadamardDesign<points=[0, 1, 2, 3, 4, 5, 6], blocks=[[0, 1, 2], [0, 3, 4], [0, 5, 6], [1, 3, 5], [1, 4, 6], [2, 3, 6], [2, 4, 5]]>

    REFERENCES:

    - [CvL] P. Cameron, J. H. van Lint, Designs, graphs, codes and
      their links, London Math. Soc., 1991.
    """
    from sage.combinat.matrices.hadamard_matrix import hadamard_matrix
    from sage.matrix.constructor import matrix
    H = hadamard_matrix(n+1)
    H1 = H.matrix_from_columns(range(1,n+1))
    H2 = H1.matrix_from_rows(range(1,n+1))
    J = matrix(ZZ,n,n,[1]*n*n)
    MS = J.parent()
    A = MS((H2+J)/2) # convert -1's to 0's; coerce entries to ZZ
    # A is the incidence matrix of the block design
    return IncidenceStructureFromMatrix(A,name="HadamardDesign")

def BlockDesign(max_pt, blks, name=None, test=True):
    """
    Returns an instance of the :class:`IncidenceStructure` class.

    Requires each B in blks to be contained in range(max_pt). Does not check if
    the result is a block design.

    EXAMPLES::

        sage: BlockDesign(7,[[0,1,2],[0,3,4],[0,5,6],[1,3,5],[1,4,6],[2,3,6],[2,4,5]], name="Fano plane")
        Incidence structure with 7 points and 7 blocks
        sage: print BlockDesign(7,[[0,1,2],[0,3,4],[0,5,6],[1,3,5],[1,4,6],[2,3,6],[2,4,5]], name="Fano plane")
        Fano plane<points=[0, 1, 2, 3, 4, 5, 6], blocks=[[0, 1, 2], [0, 3, 4], [0, 5, 6], [1, 3, 5], [1, 4, 6], [2, 3, 6], [2, 4, 5]]>
    """
    nm = name
    if nm is None and test:
        nm = "BlockDesign"
    BD = BlockDesign_generic( range(max_pt), blks, name=nm, test=test )
    if not test:
        return BD
    else:
        pars = BD.parameters(t=2)
        if BD.block_design_checker(pars[0],pars[1],pars[2],pars[3]):
            return BD
        else:
            raise TypeError("parameters are not those of a block design.")

# Possibly in the future there will be methods which apply to block designs and
# not incidence structures. None have been implemented yet though. The class
# name BlockDesign_generic is reserved in the name space in case more
# specialized methods are implemented later. In that case, BlockDesign_generic
# should inherit from IncidenceStructure.
BlockDesign_generic = IncidenceStructure

