#include <stdio.h>
#include <string.h>
#include <math.h>
#include <float.h>
#include <algorithm>

using std::min;
using std::max;

// Enumerate the rectangular generalization of "Göbel strip" / "Göbel square" style packings of units squares in a square
// by David Ellsworth, 2025-01-27 and 2025-12-10

int main(int argc, char* argv[])
{
//#define PRINT_DURING_INITIAL_SCAN
    const int MAX_N = 2117;
    double bestSforN[MAX_N+1];
    struct {
        double s;
        int width, height;
        int topLeft, top, topRight, right, bottomRight, bottom, bottomLeft, left;
    } bestforN[MAX_N+1];
    memset(bestforN, 0, sizeof(*bestforN) * (MAX_N+1));
    for (int n=0; n<=MAX_N; n++)
        bestSforN[n] = DBL_MAX;
    double sqrt2 = sqrt(2.);
    /*int corners[4];
    int spaces [4];*/
    for (int i=2; i<=45; i++)
    {
        for (int topLeft=1; topLeft<i; topLeft++)
        for (int top=0; topLeft + top < i; top++)
        {
            if (top > 1)
                continue;
            int topRight = i - (topLeft + top);
            for (int right=-1; topRight + right < i; right++)
            {
                if (right > 1)
                    continue;
                int bottomRight = i - (topRight + right);
                if (bottomRight < topLeft)
                    continue;
                for (int bottom=0; bottom<=1; bottom++)
                {
                    int bottomLeft = i - (bottomRight + bottom);
                    if (bottomLeft == 0)
                        continue;
                    int left = i - (bottomLeft + topLeft);
                    if (left < 0 || left > 1)
                        continue;

                    double topLeftDiag     = (topLeft    +1)/2.;
                    double topRightDiag    = (topRight   +1)/2.;
                    double bottomRightDiag = (bottomRight+1)/2.;
                    double bottomLeftDiag  = (bottomLeft +1)/2.;

                    double width  = (i + 1 - topLeftDiag  - bottomRightDiag) * sqrt2;
                    double height = (i + 1 - topRightDiag - bottomLeftDiag ) * sqrt2;

                    if (width >= 1 && height >= 1)
                    {
                        int widthInt  = (int)floor(width);
                        int heightInt = (int)floor(height);
                        double widthFrac  = width  - widthInt;
                        double heightFrac = height - heightInt;

                        double s0, s1;
                        int width0, height0;
                        int width1, height1;

                        width0 = widthInt;
                        s0 = topLeftDiag + bottomRightDiag + width0 / sqrt2;
                        //height0 = (int)floor((s0 - topRightDiag - bottomLeftDiag) * sqrt2);
                        height0 = (int)floor(width0 + (topLeftDiag + bottomRightDiag - topRightDiag - bottomLeftDiag) * sqrt2);

                        height1 = heightInt;
                        s1 = topRightDiag + bottomLeftDiag + height1 / sqrt2;
                        //width1 = (int)floor((s1 - topLeftDiag - bottomRightDiag) * sqrt2);
                        width1 = (int)floor(height1 + (topRightDiag + bottomLeftDiag - topLeftDiag - bottomRightDiag) * sqrt2);

                        if (width0>0 && height0>0)
                        {
                            int n =
                                topLeft     * (topLeft    +1) / 2 +
                                topRight    * (topRight   +1) / 2 + (right < 0 ? right : 0) +
                                bottomRight * (bottomRight+1) / 2 +
                                bottomLeft  * (bottomLeft +1) / 2 +
                                width0 * height0;
                            if (s0 < ceil(sqrt((double)n)))
                            {
                                bool squeezable = width0 != height0 && ((topLeft ^ bottomRight) & 1);
                                bool rotSym =
                                    height0 % 2 == 0 && topRight == bottomLeft && min(topLeft, bottomRight)+1 == max(topLeft, bottomRight) && (min(topLeft, bottomRight) & 1) ||
                                    width0  % 2 == 0 && topLeft == bottomRight && min(topRight, bottomLeft)+1 == max(topRight, bottomLeft) && (min(topRight, bottomLeft) & 1);
#ifdef PRINT_DURING_INITIAL_SCAN
                                printf("s(%d) = %1.15f: %d x %d: %d,(%d),%d,(%d),%d,(%d),%d,(%d)\n", n, s0, width0, height0, topLeft, top, topRight, right, bottomRight, bottom, bottomLeft, left, rotSym ? " - can have rotational symmetry" : "");
#endif
                                if (bestSforN[n] >= s0 || squeezable && !bestforN[n].width)
                                {
                                    bestSforN[n] = s0;
                                    bestforN[n].s           = s0;
                                    bestforN[n].width       = width0;
                                    bestforN[n].height      = height0;
                                    bestforN[n].topLeft     = topLeft;
                                    bestforN[n].top         = top;
                                    bestforN[n].topRight    = topRight;
                                    bestforN[n].right       = right;
                                    bestforN[n].bottomRight = bottomRight;
                                    bestforN[n].bottom      = bottom;
                                    bestforN[n].bottomLeft  = bottomLeft;
                                    bestforN[n].left        = left;

                                    for (int i1 = i, n1 = n;;)
                                    {
                                        n1 += i1 * 2 + 1;
                                        i1++;
                                        if (n1 > MAX_N) break;
                                        bestSforN[n1] = bestforN[n1].s = s0 + (i1 - i);
                                    }
                                }
                            }
                        }

                        if ((width1 != width0 || height1 != height0) && width1>0 && height1>0)
                        {
                            int n =
                                topLeft     * (topLeft    +1) / 2 +
                                topRight    * (topRight   +1) / 2 + (right < 0 ? right : 0) +
                                bottomRight * (bottomRight+1) / 2 +
                                bottomLeft  * (bottomLeft +1) / 2 +
                                width1 * height1;
                            if (s1 < ceil(sqrt((double)n)))
                            {
                                bool squeezable = width1 != height1 && ((topRight ^ bottomLeft) & 1);
                                bool rotSym =
                                    height1 % 2 == 0 && topRight == bottomLeft && min(topLeft, bottomRight)+1 == max(topLeft, bottomRight) && (min(topLeft, bottomRight) & 1) ||
                                    width1  % 2 == 0 && topLeft == bottomRight && min(topRight, bottomLeft)+1 == max(topRight, bottomLeft) && (min(topRight, bottomLeft) & 1);
#ifdef PRINT_DURING_INITIAL_SCAN
                                printf("s(%d) = %1.15f: %d x %d: %d,(%d),%d,(%d),%d,(%d),%d,(%d)%s\n", n, s1, width1, height1, topLeft, top, topRight, right, bottomRight, bottom, bottomLeft, left, rotSym ? " - can have rotational symmetry" : "");
#endif
                                if (bestSforN[n] >= s1 || squeezable && !bestforN[n].width)
                                {
                                    bestSforN[n] = s1;
                                    bestforN[n].s           = s1;
                                    bestforN[n].width       = width1;
                                    bestforN[n].height      = height1;
                                    bestforN[n].topLeft     = topLeft;
                                    bestforN[n].top         = top;
                                    bestforN[n].topRight    = topRight;
                                    bestforN[n].right       = right;
                                    bestforN[n].bottomRight = bottomRight;
                                    bestforN[n].bottom      = bottom;
                                    bestforN[n].bottomLeft  = bottomLeft;
                                    bestforN[n].left        = left;

                                    for (int i1 = i, n1 = n;;)
                                    {
                                        n1 += i1 * 2 + 1;
                                        i1++;
                                        if (n1 > MAX_N) break;
                                        bestSforN[n1] = bestforN[n1].s = s1 + (i1 - i);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    for (int n=1; n<=MAX_N; n++)
    {
        if (bestSforN[n] != DBL_MAX)
        {
            printf("s(%4d) = %18.15f", n, bestforN[n].s);
            if (bestforN[n].width)
            {
                double topLeftDiag     = (bestforN[n].topLeft    +1)/2.;
                double topRightDiag    = (bestforN[n].topRight   +1)/2.;
                double bottomRightDiag = (bestforN[n].bottomRight+1)/2.;
                double bottomLeftDiag  = (bestforN[n].bottomLeft +1)/2.;
                double s0 = topLeftDiag  + bottomRightDiag + bestforN[n].width  / sqrt2;
                double s1 = topRightDiag + bottomLeftDiag  + bestforN[n].height / sqrt2;
                bool squeezable = bestforN[n].width != bestforN[n].height && ((s0 > s1 ? (bestforN[n].topLeft ^ bestforN[n].bottomRight) : (bestforN[n].topRight ^ bestforN[n].bottomLeft)) & 1);
                bool rotSym =
                    bestforN[n].height % 2 == 0 && bestforN[n].topRight == bestforN[n].bottomLeft && min(bestforN[n].topLeft, bestforN[n].bottomRight)+1 == max(bestforN[n].topLeft, bestforN[n].bottomRight) && (min(bestforN[n].topLeft, bestforN[n].bottomRight) & 1) ||
                    bestforN[n].width  % 2 == 0 && bestforN[n].topLeft == bestforN[n].bottomRight && min(bestforN[n].topRight, bestforN[n].bottomLeft)+1 == max(bestforN[n].topRight, bestforN[n].bottomLeft) && (min(bestforN[n].topRight, bestforN[n].bottomLeft) & 1);
                printf(": %2d x %2d: %2d,(%d),%2d,(%2d),%2d,(%d),%2d,(%d)", bestforN[n].width, bestforN[n].height, bestforN[n].topLeft, bestforN[n].top, bestforN[n].topRight, bestforN[n].right, bestforN[n].bottomRight, bestforN[n].bottom, bestforN[n].bottomLeft, bestforN[n].left);
                if (squeezable)
                    printf(" - squeezable (%1.15f)", fabs(s1 - s0));
                else
                    printf("                                 ");
                if (rotSym)
                    printf(" - can have rotational symmetry");
            }
            putchar('\n');
        }
    }
    return 0;
}
