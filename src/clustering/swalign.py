#!/usr/bin/env python
'''
I took this code from the module swalign and I adapted it to Python 3. I also removed the part not useful
in our use case. You can find the original code here https://pypi.org/project/swalign/
'''
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class NucleotideScoringMatrix(object):
    def __init__(self, match=1, mismatch=-1):
        self.match = match
        self.mismatch = mismatch

    def score(self, one, two, wildcard=None):
        if wildcard and (one in wildcard or two in wildcard):
            return self.match

        if one == two:
            return self.match
        return self.mismatch


class Matrix(object):
    def __init__(self, rows, cols, init=None):
        self.rows = rows
        self.cols = cols
        self.values = [init, ] * rows * cols

    def get(self, row, col):
        return self.values[(row * self.cols) + col]

    def set(self, row, col, val):
        self.values[(row * self.cols) + col] = val


class LocalAlignment(object):
    def __init__(self, scoring_matrix, gap_penalty=-1, gap_extension_penalty=-1, gap_extension_decay=0.0,
                 prefer_gap_runs=True, verbose=False, globalalign=False, wildcard=None, full_query=False):
        self.scoring_matrix = scoring_matrix
        self.gap_penalty = gap_penalty
        self.gap_extension_penalty = gap_extension_penalty
        self.gap_extension_decay = gap_extension_decay
        self.verbose = verbose
        self.prefer_gap_runs = prefer_gap_runs
        self.globalalign = globalalign
        self.wildcard = wildcard
        self.full_query = full_query

    def align(self, ref, query, ref_name='', query_name='', rc=False):
        orig_ref = ref
        orig_query = query

        ref = ref.upper()
        query = query.upper()

        matrix = Matrix(len(query) + 1, len(ref) + 1, (0, ' ', 0))
        for row in range(1, matrix.rows):
            matrix.set(row, 0, (0, 'i', 0))

        for col in range(1, matrix.cols):
            matrix.set(0, col, (0, 'd', 0))

        max_val = 0
        max_row = 0
        max_col = 0

        # calculate matrix
        for row in range(1, matrix.rows):
            for col in range(1, matrix.cols):
                mm_val = matrix.get(row - 1, col - 1)[0] + self.scoring_matrix.score(query[row - 1], ref[col - 1],
                                                                                     self.wildcard)

                ins_run = 0
                del_run = 0

                if matrix.get(row - 1, col)[1] == 'i':
                    ins_run = matrix.get(row - 1, col)[2]
                    if matrix.get(row - 1, col)[0] == 0:
                        # no penalty to start the alignment
                        ins_val = 0
                    else:
                        if not self.gap_extension_decay:
                            ins_val = matrix.get(row - 1, col)[0] + self.gap_extension_penalty
                        else:
                            ins_val = matrix.get(row - 1, col)[0] + min(0,
                                                                        self.gap_extension_penalty + ins_run * self.gap_extension_decay)
                else:
                    ins_val = matrix.get(row - 1, col)[0] + self.gap_penalty

                if matrix.get(row, col - 1)[1] == 'd':
                    del_run = matrix.get(row, col - 1)[2]
                    if matrix.get(row, col - 1)[0] == 0:
                        # no penalty to start the alignment
                        del_val = 0
                    else:
                        if not self.gap_extension_decay:
                            del_val = matrix.get(row, col - 1)[0] + self.gap_extension_penalty
                        else:
                            del_val = matrix.get(row, col - 1)[0] + min(0,
                                                                        self.gap_extension_penalty + del_run * self.gap_extension_decay)

                else:
                    del_val = matrix.get(row, col - 1)[0] + self.gap_penalty

                if self.globalalign or self.full_query:
                    cell_val = max(mm_val, del_val, ins_val)
                else:
                    cell_val = max(mm_val, del_val, ins_val, 0)

                if not self.prefer_gap_runs:
                    ins_run = 0
                    del_run = 0

                if del_run and cell_val == del_val:
                    val = (cell_val, 'd', del_run + 1)
                elif ins_run and cell_val == ins_val:
                    val = (cell_val, 'i', ins_run + 1)
                elif cell_val == mm_val:
                    val = (cell_val, 'm', 0)
                elif cell_val == del_val:
                    val = (cell_val, 'd', 1)
                elif cell_val == ins_val:
                    val = (cell_val, 'i', 1)
                else:
                    val = (0, 'x', 0)

                if val[0] >= max_val:
                    max_val = val[0]
                    max_row = row
                    max_col = col

                matrix.set(row, col, val)

        # backtrack
        if self.globalalign:
            # backtrack from last cell
            row = matrix.rows - 1
            col = matrix.cols - 1
            val = matrix.get(row, col)[0]
        elif self.full_query:
            # backtrack from max in last row
            row = matrix.rows - 1
            max_val = 0
            col = 0
            for c in range(1, matrix.cols):
                if matrix.get(row, c)[0] > max_val:
                    col = c
                    max_val = matrix.get(row, c)[0]
            col = matrix.cols - 1
            val = matrix.get(row, col)[0]
        else:
            # backtrack from max
            row = max_row
            col = max_col
            val = max_val

        op = ''
        aln = []

        path = []
        while True:
            val, op, runlen = matrix.get(row, col)

            if self.globalalign:
                if row == 0 and col == 0:
                    break
            elif self.full_query:
                if row == 0:
                    break
            else:
                if val <= 0:
                    break

            path.append((row, col))
            aln.append(op)

            if op == 'm':
                row -= 1
                col -= 1
            elif op == 'i':
                row -= 1
            elif op == 'd':
                col -= 1
            else:
                break

        aln.reverse()

        if self.verbose:
            self.dump_matrix(ref, query, matrix, path)
            print(aln)
            print((max_row, max_col), max_val)

        cigar = _reduce_cigar(aln)
        # return Alignment(orig_query, orig_ref, row, col, cigar, max_val, ref_name, query_name, rc, self.globalalign, self.wildcard)
        return max_val


def _reduce_cigar(operations):
    count = 1
    last = None
    ret = []
    for op in operations:
        if last and op == last:
            count += 1
        elif last:
            ret.append((count, last.upper()))
            count = 1
        last = op

    if last:
        ret.append((count, last.upper()))
    return ret
