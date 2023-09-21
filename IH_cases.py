import os
import re


def roi(plus, minus, k = 1.8):
    return f'ROI:{(plus * (k - 1) - minus) * (100 / (plus + minus)): .2f}%'

def percantage(plus, minus):
    return round(plus / (plus + minus),  3)

def check_scores_and_odds(file_name, period, minute, t1_p1, t2_p1, t1_p2, t2_p2, t1_p3, t2_p3, coef1, coef2, case = ''):
    with open(file_name, 'r') as file:
        data = file.read()
        matches = data.split('\n')
        lst_list = []
        plus = minus = 0
        ind_plus1 = ind_minus1 = ind_plus2 = ind_minus2 = 0
        scanned = 0
        empty_bet = ''
        print(file_name, period, minute, t1_p1, t2_p1, t1_p2, t2_p2, t1_p3, t2_p3, coef1, coef2)
        for num,match in enumerate(matches):
            try:
                if num > 8000:
                    break
                cleaned_str = re.sub(r"[\[\]',]", "", match)
                lst = cleaned_str.split()
                lst_list.append(lst)
                try:
                    index_1st, index_2nd, index_3rd = lst.index('1ST'), lst.index('2ND'), lst.index('3RD')
                    t1_h1, t1_h2, t2_h1, t2_h2, t1_h3, t2_h3 = int(lst[index_1st + 2]), int(lst[index_2nd + 2]),\
                        int(lst[index_1st + 4]), int(lst[index_2nd + 4]), int(lst[index_3rd + 2]), int(lst[index_3rd + 4])
                except:
                    continue

                try:
                    index_odds = lst.index('ODDS')
                    coef_list = lst[index_odds:]
                    k1, k2 = float(coef_list[2]) if coef_list[2] != '-' else float(coef_list[8]), float(coef_list[6]) if \
                        coef_list[6] != '-' else float(coef_list[12])
                except:
                    k1 = k2 = 1


                try:
                    if isinstance(index_1st, int) and isinstance(index_2nd, int) and isinstance(index_odds, int) and isinstance(k1, float):
                        scanned += 1
                except:
                    continue
                x = 1
                if coef1 == 0:
                    k1 = 2
                    coef1 = 2
                    x = 3

                if period == 1 and t1_p1 == 0 and t2_p1 == 0:
                    if coef1 - 0.35*x <= k1 <= coef1 + 0.35*x:
                        if t1_h1 + t2_h1 > 0:
                            plus += 1
                        else:
                            minus += 1


                if period == 1  and t1_p1 + t2_p1 > 0:
                    if coef1 - 0.35*x <= k1 <= coef1 + 0.35*x:
                        if t1_h1 == t1_p1 and t2_h1 == t2_p1:
                            minus += 1
                        else:
                            plus += 1


                if period == 2 and t1_p2 == 0 and t2_p2 == 0:
                    if  coef1 - 0.35*x <= k1 <= coef1*x + 0.35:
                        if t1_h1 == t1_p1 and t2_h1 == t2_p1:
                            if t1_h2 + t2_h2 > 0:
                                plus += 1
                            else:
                                minus += 1


                if period == 2  and t1_p2 + t2_p2 > 0:
                    if coef1 - 0.35*x <= k1 <= coef1 + 0.35*x:
                        if t1_h1 == t1_p1 and t2_h1 == t2_p1 and t1_h2 == t2_p1 and t2_h2 == t2_p2:
                            minus += 1
                        else:
                            plus += 1



                if period == 3 and t1_p3 == 0 and t2_p3 == 0:
                    if coef1 - 0.35*x <= k1 <= coef1 + 0.35*x:
                        if t1_h1 == t1_p1 and t2_h1 == t2_p1 and t1_h2 == t1_p2 and t2_h2 == t2_p2:
                            if t1_h3 + t2_h3 > 0:
                                plus += 1
                            else:
                                minus += 1


                if period == 2 and t1_p1 == 0 and t1_p2 == 0 and case == 'ind1':
                    if coef1 - 0.35*x <= k1 <= coef1 + 0.35*x:
                        if t2_h1 == t2_p1:
                            if t1_h2 + t1_h3 >0:
                                ind_plus1 += 1
                            else:
                                ind_minus1 += 1

                if period == 2 and t2_p1 == 0 and t2_p2 == 0 and case == 'ind2':
                    if coef1 - 0.35*x <= k1 <= coef1 + 0.35*x:
                        if t1_h1 == t1_p1:
                            if t2_h2 + t2_h3 >0:
                                ind_plus1 += 1
                            else:
                                ind_minus1 += 1

                # if 3<k1 <4:
                #     deutch += 1
                #     if t1_h1 == 1 and t2_h1 == 1 and t1_h2 == 1 and t2_h2 == 0:
                #         if t1_h3 + t2_h3 > 0    :
                #             plus += 1
                #         else:
                #             minus += 1

            except Exception as s:
                print(s)
                continue


        print(scanned)
        print('Plus::',plus,'Minus::', minus)
        try:
            print(roi(plus, minus, k =1.1))
            print(percantage(plus, minus))

        except:
            True
        print()

        if (plus >= 10 and  percantage(plus, minus)> 0.85) or \
                (plus > 50 and percantage(plus, minus)> 0.85) or\
                (plus > 100 and percantage(plus, minus)> 0.85)  or\
                (minus == 0 and plus > 4):
            if case == '':
                return (f'{percantage(plus, minus)}', f'Period: {period}', f'+{plus}  -{minus}')

        if case == 'ind1' and percantage(ind_plus1, ind_minus1) > 0.9:

            return (f'ind1 total',f'+{ind_plus1}  -{ind_minus1}')

        if case == 'ind2' and percantage(ind_plus1, ind_minus1) > 0.9:
            return (f'ind2 total', f'+{ind_plus1}  -{ind_minus1}')





